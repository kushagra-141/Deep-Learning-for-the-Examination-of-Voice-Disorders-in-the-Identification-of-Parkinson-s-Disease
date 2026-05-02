"""P3.5-02: LLM provider abstraction.

A single ``LLMProvider`` Protocol covers Groq, Gemini, and OpenRouter — all
three speak the OpenAI Chat Completions schema, so we can stream against any
of them through one async iterator.

Streaming model: providers yield :class:`ChatChunk` objects. A chunk may carry
text deltas, an in-progress tool-call delta (whose JSON arguments arrive
piecemeal across chunks), a finish reason, or a final usage record. The
orchestrator is responsible for reassembling tool-call argument fragments
across chunks.
"""
from __future__ import annotations

from typing import Any, AsyncIterator, Literal, Protocol, runtime_checkable

from pydantic import BaseModel


# ── Errors ──────────────────────────────────────────────────────────────────

class LLMUnavailable(Exception):
    """Base class for all provider-side failures the router can react to."""


class RateLimitError(LLMUnavailable):
    """The provider returned 429 / quota exceeded."""


class UpstreamError(LLMUnavailable):
    """Generic 5xx or transport error from the provider."""


class LLMTimeoutError(LLMUnavailable):
    """The provider did not respond before ``LLM_TIMEOUT_S`` elapsed."""


# ── Schemas ─────────────────────────────────────────────────────────────────

class ToolDef(BaseModel):
    """OpenAI-format tool definition. ``parameters`` is a JSON Schema object."""

    name: str
    description: str
    parameters: dict[str, Any]


class ToolCallDelta(BaseModel):
    """A streaming fragment of a tool call.

    The provider may emit the call across many chunks; ``index`` lets the
    orchestrator group fragments belonging to the same call. ``arguments`` is
    a partial JSON string that should be concatenated in order.
    """

    index: int = 0
    id: str | None = None
    name: str | None = None
    arguments: str | None = None


class ChatMessage(BaseModel):
    """A message in the chat history.

    ``role="tool"`` messages MUST carry ``tool_call_id`` matching the call they
    answer; their ``content`` is the JSON string of the tool result.
    """

    role: Literal["system", "user", "assistant", "tool"]
    content: str | None = None
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    name: str | None = None


class ChatUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatChunk(BaseModel):
    """A single streaming event from a provider."""

    delta_text: str | None = None
    tool_call: ToolCallDelta | None = None
    finish_reason: Literal["stop", "tool_calls", "length", "content_filter"] | None = None
    usage: ChatUsage | None = None


# ── Protocol ────────────────────────────────────────────────────────────────

@runtime_checkable
class LLMProvider(Protocol):
    """Streaming chat provider.

    Implementations must:
    - Be safe to share across requests (no per-call mutable state).
    - Translate provider-specific errors to :class:`LLMUnavailable` subclasses
      so the router can react uniformly.
    - Honour ``LLM_TIMEOUT_S`` from settings; a hung connection is a
      :class:`LLMTimeoutError`.
    """

    name: str

    async def stream_chat(
        self,
        *,
        model: str,
        messages: list[ChatMessage],
        tools: list[ToolDef] | None = None,
        max_tokens: int = 600,
        temperature: float = 0.2,
    ) -> AsyncIterator[ChatChunk]:
        """Yield chunks until the provider signals completion.

        Implementations are async generators; ``async for`` over the result is
        the only supported access pattern.
        """
        ...
