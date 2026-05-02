"""Shared OpenAI-compatible streaming client.

Groq, Gemini (via the OpenAI-compatible endpoint), and OpenRouter all return
the same streaming chunk shape, so we share one implementation and inject
``base_url`` / ``api_key`` / ``name`` per provider.
"""
from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator

import httpx
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
)
from openai import (
    RateLimitError as _OpenAIRateLimit,
)
from openai import AsyncOpenAI

from app.llm.providers.base import (
    ChatChunk,
    ChatMessage,
    ChatUsage,
    LLMTimeoutError,
    RateLimitError,
    ToolCallDelta,
    ToolDef,
    UpstreamError,
)


def _to_openai_messages(messages: list[ChatMessage]) -> list[dict[str, Any]]:
    """Convert our :class:`ChatMessage` list to the dict shape the SDK expects."""
    out: list[dict[str, Any]] = []
    for m in messages:
        body: dict[str, Any] = {"role": m.role}
        if m.content is not None:
            body["content"] = m.content
        if m.tool_calls:
            body["tool_calls"] = m.tool_calls
        if m.tool_call_id:
            body["tool_call_id"] = m.tool_call_id
        if m.name:
            body["name"] = m.name
        out.append(body)
    return out


def _to_openai_tools(tools: list[ToolDef] | None) -> list[dict[str, Any]] | None:
    if not tools:
        return None
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            },
        }
        for t in tools
    ]


class OpenAICompatProvider:
    """Base class for any provider with an OpenAI-compatible Chat Completions API."""

    name: str

    def __init__(
        self,
        *,
        name: str,
        api_key: str,
        base_url: str,
        timeout_s: float,
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        self.name = name
        self._timeout_s = timeout_s
        # Inject extra headers (Groq's "data_retention=off", etc.) via the
        # default httpx client so they ride along on every call.
        http_client: httpx.AsyncClient | None = None
        if extra_headers:
            http_client = httpx.AsyncClient(headers=extra_headers, timeout=timeout_s)
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout_s,
            http_client=http_client,
            max_retries=0,  # Router handles retries — keep this layer dumb.
        )

    async def stream_chat(
        self,
        *,
        model: str,
        messages: list[ChatMessage],
        tools: list[ToolDef] | None = None,
        max_tokens: int = 600,
        temperature: float = 0.2,
    ) -> AsyncIterator[ChatChunk]:
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": _to_openai_messages(messages),
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        oai_tools = _to_openai_tools(tools)
        if oai_tools:
            kwargs["tools"] = oai_tools
            kwargs["tool_choice"] = "auto"

        try:
            stream = await asyncio.wait_for(
                self._client.chat.completions.create(**kwargs),
                timeout=self._timeout_s,
            )
        except asyncio.TimeoutError as exc:
            raise LLMTimeoutError(f"{self.name}: connect timed out") from exc
        except APITimeoutError as exc:
            raise LLMTimeoutError(f"{self.name}: timed out") from exc
        except _OpenAIRateLimit as exc:
            raise RateLimitError(f"{self.name}: rate limit") from exc
        except (APIConnectionError, APIStatusError) as exc:
            raise UpstreamError(f"{self.name}: {exc}") from exc

        try:
            async for raw in _iter_with_timeout(stream, self._timeout_s):
                yield _translate_chunk(raw)
        except asyncio.TimeoutError as exc:
            raise LLMTimeoutError(f"{self.name}: stalled mid-stream") from exc
        except _OpenAIRateLimit as exc:
            raise RateLimitError(f"{self.name}: rate limit mid-stream") from exc
        except (APIConnectionError, APIStatusError) as exc:
            raise UpstreamError(f"{self.name}: {exc}") from exc


async def _iter_with_timeout(stream: Any, timeout_s: float) -> AsyncIterator[Any]:
    """Yield from ``stream`` with a per-chunk timeout to detect mid-stream stalls."""
    aiter = stream.__aiter__()
    while True:
        try:
            chunk = await asyncio.wait_for(aiter.__anext__(), timeout=timeout_s)
        except StopAsyncIteration:
            return
        yield chunk


def _translate_chunk(raw: Any) -> ChatChunk:
    """Map an OpenAI streaming chunk to our :class:`ChatChunk`."""
    delta_text: str | None = None
    tool_call: ToolCallDelta | None = None
    finish_reason: str | None = None
    usage: ChatUsage | None = None

    choices = getattr(raw, "choices", None) or []
    if choices:
        choice = choices[0]
        delta = getattr(choice, "delta", None)
        if delta is not None:
            delta_text = getattr(delta, "content", None) or None
            tcs = getattr(delta, "tool_calls", None)
            if tcs:
                tc = tcs[0]
                fn = getattr(tc, "function", None)
                tool_call = ToolCallDelta(
                    index=getattr(tc, "index", 0) or 0,
                    id=getattr(tc, "id", None),
                    name=getattr(fn, "name", None) if fn else None,
                    arguments=getattr(fn, "arguments", None) if fn else None,
                )
        finish_reason = getattr(choice, "finish_reason", None)

    raw_usage = getattr(raw, "usage", None)
    if raw_usage is not None:
        usage = ChatUsage(
            prompt_tokens=getattr(raw_usage, "prompt_tokens", 0) or 0,
            completion_tokens=getattr(raw_usage, "completion_tokens", 0) or 0,
            total_tokens=getattr(raw_usage, "total_tokens", 0) or 0,
        )

    return ChatChunk(
        delta_text=delta_text,
        tool_call=tool_call,
        finish_reason=finish_reason if finish_reason in ("stop", "tool_calls", "length", "content_filter") else None,
        usage=usage,
    )
