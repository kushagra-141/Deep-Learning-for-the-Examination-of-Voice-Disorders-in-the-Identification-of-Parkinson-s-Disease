"""P3.5-07: Chat orchestrator.

Drives the stream → tool-call → execute → resume loop described in
``docs/06_LLM_INTEGRATION_LLD.md`` §6.5.5.

Flow per user turn:

1. Charge an empty budget probe (``budget.assert_budget``); raise 429 early on cap hit.
2. Look up cache iff this turn could plausibly be cacheable (no tools used yet).
3. Build the message list (system prompt + history + new user message).
4. Stream from the provider router. Accumulate text deltas; reassemble tool-call
   argument fragments across chunks.
5. On ``finish_reason == "tool_calls"``: execute every accumulated call, append
   the resulting ``tool`` messages to the history, and re-enter the inner loop.
6. On ``finish_reason in ("stop", "length")``: validate the assembled text via
   :mod:`app.llm.validator`, persist the session, optionally store the cache
   entry (only when no tools were called this turn), commit token usage, and
   return.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, AsyncIterator, Literal

import structlog

from app.core.config import get_settings
from app.llm import budget, cache
from app.llm.factory import get_router, model_for
from app.llm.providers import (
    ChatChunk,
    ChatMessage,
    ChatUsage,
    LLMUnavailable,
    ToolCallDelta,
)
from app.llm.session import load_history, new_session_id, save_history
from app.llm.tools import ChatContext, FeatureName, ToolRegistry, ToolValidationError, build_default_registry
from app.llm.validator import check_assistant, check_narrator

log = structlog.get_logger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"
HELP_CORPUS_PATH = Path(__file__).parent / "help_corpus.md"

MAX_TOOL_TURNS = 4  # safety cap — bail out if the LLM keeps calling tools


# ── Public events ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class DeltaEvent:
    text: str


@dataclass(frozen=True)
class ToolEvent:
    name: str
    status: Literal["called", "ok", "error"]
    detail: str | None = None


@dataclass(frozen=True)
class DoneEvent:
    text: str
    cached: bool = False
    usage: ChatUsage | None = None


@dataclass(frozen=True)
class ErrorEvent:
    message: str


OrchestratorEvent = DeltaEvent | ToolEvent | DoneEvent | ErrorEvent


# ── Prompt rendering ───────────────────────────────────────────────────────

def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _render_explainer_system(prediction_payload: dict[str, Any] | None) -> str:
    template = _read(PROMPTS_DIR / "explainer_system.md")
    payload = json.dumps(prediction_payload or {}, ensure_ascii=False, indent=2)
    return template.replace("{context_json}", payload)


def _render_help_system() -> str:
    template = _read(PROMPTS_DIR / "help_system.md")
    return template.replace("{help_corpus_md}", _read(HELP_CORPUS_PATH))


def _render_narrator_system(prediction_payload: dict[str, Any]) -> str:
    template = _read(PROMPTS_DIR / "narrator_system.md")
    payload = json.dumps(prediction_payload, ensure_ascii=False, indent=2)
    return template.replace("{prediction_payload_json}", payload)


# ── Tool-call reassembly ───────────────────────────────────────────────────

@dataclass
class _PendingToolCall:
    """Buffer for a tool call while its argument JSON arrives in fragments."""

    index: int
    id: str | None = None
    name: str | None = None
    arguments_buffer: str = ""

    def absorb(self, delta: ToolCallDelta) -> None:
        if delta.id and not self.id:
            self.id = delta.id
        if delta.name and not self.name:
            self.name = delta.name
        if delta.arguments:
            self.arguments_buffer += delta.arguments

    def parsed_arguments(self) -> dict[str, Any]:
        if not self.arguments_buffer:
            return {}
        try:
            parsed = json.loads(self.arguments_buffer)
        except json.JSONDecodeError as exc:
            raise ToolValidationError(
                f"Tool {self.name!r} produced unparseable arguments: {exc}",
            ) from exc
        if not isinstance(parsed, dict):
            raise ToolValidationError(f"Tool {self.name!r} arguments must be an object")
        return parsed


# ── Orchestrator ───────────────────────────────────────────────────────────

class ChatOrchestrator:
    """Singleton-friendly: holds the registry and router; per-call state lives in args."""

    def __init__(
        self,
        registry: ToolRegistry | None = None,
    ) -> None:
        self.registry = registry or build_default_registry()
        self.router = get_router()

    def get_or_create_session(self, session_id: str | None) -> str:
        return session_id or new_session_id()

    def build_context(
        self,
        *,
        session_id: str,
        client_fingerprint: str,
        prediction_payload: dict[str, Any] | None,
        model_manager: Any | None,
    ) -> ChatContext:
        prediction_id: str | None = None
        prediction_features: dict[str, float] | None = None
        if prediction_payload:
            prediction_id = prediction_payload.get("prediction_id") or None
            features = prediction_payload.get("features")
            if isinstance(features, dict):
                prediction_features = {k: float(v) for k, v in features.items()}
        return ChatContext(
            session_id=session_id,
            client_fingerprint=client_fingerprint,
            prediction_id=prediction_id,
            prediction_features=prediction_features,
            prediction_payload=prediction_payload,
            model_manager=model_manager,
        )

    async def run(
        self,
        *,
        feature: FeatureName,
        user_message: str,
        ctx: ChatContext,
    ) -> AsyncIterator[OrchestratorEvent]:
        settings = get_settings()
        provider_name = self.router.primary.name
        model_name = model_for(feature, provider_name)
        max_tokens = int(settings.LLM_DAILY_TOKEN_BUDGET and 600)

        # 1. Budget probe
        try:
            await budget.assert_budget(ctx.client_fingerprint)
        except budget.BudgetExceeded as exc:
            yield ErrorEvent(message=f"daily token budget exceeded ({exc.scope})")
            return

        # 2. Build prompt + history
        if feature == "explainer":
            system_text = _render_explainer_system(ctx.prediction_payload)
        elif feature == "help":
            system_text = _render_help_system()
        else:
            yield ErrorEvent(message=f"feature {feature!r} is not supported by run_chat")
            return

        history = await load_history(ctx.session_id)
        history.append(ChatMessage(role="user", content=user_message))
        messages: list[ChatMessage] = [
            ChatMessage(role="system", content=system_text),
            *history,
        ]
        tools = self.registry.for_feature(feature)

        # 3. Cache lookup (only when this turn could be tool-free; we don't know
        #    yet whether the model will call tools, so we eagerly probe and only
        #    *store* on the no-tools branch later).
        cache_key = cache.make_key(
            feature=feature,
            model=model_name,
            messages=[m.model_dump(exclude_none=True) for m in messages],
        )
        cached = await cache.lookup(cache_key)
        if cached is not None:
            yield DeltaEvent(text=cached)
            history.append(ChatMessage(role="assistant", content=cached))
            await save_history(ctx.session_id, history)
            yield DoneEvent(text=cached, cached=True)
            return

        # 4. Streaming loop, possibly with tool round-trips.
        accumulated_text = ""
        tool_was_called = False
        last_usage: ChatUsage | None = None

        for turn in range(MAX_TOOL_TURNS):
            pending: dict[int, _PendingToolCall] = {}
            finish_reason: str | None = None
            turn_text = ""

            try:
                async for chunk in self.router.stream_chat(
                    model=model_name,
                    messages=messages,
                    tools=tools or None,
                    max_tokens=max_tokens,
                    temperature=0.2,
                ):
                    yielded_event = await self._handle_chunk(chunk, pending)
                    if yielded_event is not None:
                        yield yielded_event
                    if chunk.delta_text:
                        turn_text += chunk.delta_text
                        accumulated_text += chunk.delta_text
                    if chunk.usage is not None:
                        last_usage = chunk.usage
                    if chunk.finish_reason is not None:
                        finish_reason = chunk.finish_reason
                        break
            except LLMUnavailable as exc:
                log.warning("llm_orchestrator_provider_failed", error=str(exc))
                yield ErrorEvent(message="The assistant is taking a break — try again in a minute.")
                return

            if finish_reason in (None, "stop", "length", "content_filter"):
                # Validate, persist, cache, commit usage.
                final_text = accumulated_text
                validation = check_assistant(final_text)
                if validation.outcome == "violation":
                    final_text = validation.text
                    yield DeltaEvent(text="\n\n" + final_text)
                history.append(ChatMessage(role="assistant", content=final_text))
                await save_history(ctx.session_id, history)
                if not tool_was_called and validation.outcome != "violation":
                    await cache.store(cache_key, final_text)
                if last_usage is not None:
                    await budget.commit_tokens(
                        ctx.client_fingerprint,
                        int(last_usage.total_tokens or last_usage.completion_tokens or 0),
                    )
                yield DoneEvent(text=final_text, cached=False, usage=last_usage)
                return

            if finish_reason == "tool_calls":
                tool_was_called = True
                if not pending:
                    yield ErrorEvent(message="model signalled tool_calls but produced no calls")
                    return

                # Append the assistant turn that contained the tool calls. Per
                # OpenAI protocol, the tool result messages must reference these
                # calls by id.
                assistant_tool_calls = [
                    {
                        "id": p.id or f"call_{i}",
                        "type": "function",
                        "function": {
                            "name": p.name or "unknown",
                            "arguments": p.arguments_buffer or "{}",
                        },
                    }
                    for i, p in sorted(pending.items())
                ]
                # An assistant message with tool_calls usually has no content;
                # if the model emitted text alongside tool calls, preserve it.
                messages.append(
                    ChatMessage(
                        role="assistant",
                        content=turn_text or None,
                        tool_calls=assistant_tool_calls,
                    ),
                )

                for i, call in sorted(pending.items()):
                    name = call.name or "unknown"
                    if name == "unknown":
                        result_payload: dict[str, Any] = {"error": "missing tool name"}
                        yield ToolEvent(name=name, status="error", detail="missing tool name")
                    else:
                        try:
                            args = call.parsed_arguments()
                            result_payload = await self.registry.execute(name, args, ctx)
                            yield ToolEvent(name=name, status="ok")
                        except ToolValidationError as exc:
                            result_payload = {"error": str(exc)}
                            yield ToolEvent(name=name, status="error", detail=str(exc))

                    messages.append(
                        ChatMessage(
                            role="tool",
                            tool_call_id=call.id or f"call_{i}",
                            name=name,
                            content=json.dumps(result_payload, ensure_ascii=False),
                        ),
                    )
                # Continue outer loop — model resumes with tool outputs.
                continue

            yield ErrorEvent(message=f"unexpected finish_reason: {finish_reason}")
            return

        yield ErrorEvent(message="tool-call loop exceeded the safety cap")

    async def _handle_chunk(
        self,
        chunk: ChatChunk,
        pending: dict[int, _PendingToolCall],
    ) -> OrchestratorEvent | None:
        if chunk.tool_call is not None:
            tc = chunk.tool_call
            buf = pending.get(tc.index)
            first_fragment = buf is None
            if buf is None:
                buf = _PendingToolCall(index=tc.index)
                pending[tc.index] = buf
            buf.absorb(tc)
            if first_fragment and (tc.name or buf.name):
                return ToolEvent(name=buf.name or tc.name or "unknown", status="called")
            return None
        if chunk.delta_text:
            return DeltaEvent(text=chunk.delta_text)
        return None

    async def help_once(self, *, question: str, client_fingerprint: str) -> tuple[str, ChatUsage | None]:
        """One-shot, non-streaming help answer.

        Reuses the streaming machinery internally and accumulates the full text
        before returning. Cache-aware. Tools are not exposed to the help bot.
        """
        provider_name = self.router.primary.name
        model_name = model_for("help", provider_name)
        await budget.assert_budget(client_fingerprint)

        system_text = _render_help_system()
        messages: list[ChatMessage] = [
            ChatMessage(role="system", content=system_text),
            ChatMessage(role="user", content=question),
        ]
        cache_key = cache.make_key(
            feature="help",
            model=model_name,
            messages=[m.model_dump(exclude_none=True) for m in messages],
        )
        cached = await cache.lookup(cache_key)
        if cached is not None:
            return cached, None

        text = ""
        last_usage: ChatUsage | None = None
        async for chunk in self.router.stream_chat(
            model=model_name,
            messages=messages,
            tools=None,
            max_tokens=400,
            temperature=0.2,
        ):
            if chunk.delta_text:
                text += chunk.delta_text
            if chunk.usage is not None:
                last_usage = chunk.usage

        validation = check_assistant(text)
        final_text = validation.text if validation.outcome == "violation" else text
        if validation.outcome != "violation":
            await cache.store(cache_key, final_text)
        if last_usage is not None:
            await budget.commit_tokens(
                client_fingerprint,
                int(last_usage.total_tokens or last_usage.completion_tokens or 0),
            )
        return final_text, last_usage

    async def narrate_once(
        self,
        *,
        prediction_payload: dict[str, Any],
        client_fingerprint: str,
    ) -> tuple[str, str, ChatUsage | None]:
        """Generate a single narrator paragraph. Returns (text, model_used, usage)."""
        provider_name = self.router.primary.name
        model_name = model_for("narrator", provider_name)
        await budget.assert_budget(client_fingerprint)

        messages: list[ChatMessage] = [
            ChatMessage(role="system", content=_render_narrator_system(prediction_payload)),
            ChatMessage(role="user", content="Write the paragraph now."),
        ]
        text = ""
        last_usage: ChatUsage | None = None
        async for chunk in self.router.stream_chat(
            model=model_name,
            messages=messages,
            tools=None,
            max_tokens=300,
            temperature=0.2,
        ):
            if chunk.delta_text:
                text += chunk.delta_text
            if chunk.usage is not None:
                last_usage = chunk.usage

        validation = check_narrator(text)
        if last_usage is not None:
            await budget.commit_tokens(
                client_fingerprint,
                int(last_usage.total_tokens or last_usage.completion_tokens or 0),
            )
        return validation.text, model_name, last_usage


_orchestrator: ChatOrchestrator | None = None


def get_orchestrator() -> ChatOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = ChatOrchestrator()
    return _orchestrator
