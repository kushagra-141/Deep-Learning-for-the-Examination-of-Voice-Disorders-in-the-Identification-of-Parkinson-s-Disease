"""P3.5-03: Provider router with circuit breaker.

Tries the primary provider first; on rate-limit / 5xx / timeout, falls over to
the fallback within the same call. After three consecutive primary failures,
opens the circuit for ``CIRCUIT_OPEN_SECONDS`` and routes straight to fallback.
A successful primary call resets the failure counter.

The router itself is stateful (counters, circuit deadline) but never holds
per-request state, so it is safe to share as a singleton across the app.
"""
from __future__ import annotations

import time
from typing import AsyncIterator

import structlog

from app.llm.providers import (
    ChatChunk,
    ChatMessage,
    LLMProvider,
    LLMUnavailable,
    ToolDef,
)

log = structlog.get_logger(__name__)

CIRCUIT_OPEN_SECONDS = 60.0
CONSECUTIVE_FAILURES_TO_OPEN = 3


class ProviderRouter:
    """Primary/fallback router with a 60-s circuit on the primary."""

    def __init__(
        self,
        primary: LLMProvider,
        fallback: LLMProvider | None = None,
    ) -> None:
        self.primary = primary
        self.fallback = fallback
        self._consecutive_failures = 0
        self._circuit_open_until = 0.0

    @property
    def circuit_is_open(self) -> bool:
        return time.monotonic() < self._circuit_open_until

    def reset(self) -> None:
        """For tests."""
        self._consecutive_failures = 0
        self._circuit_open_until = 0.0

    async def stream_chat(
        self,
        *,
        model: str,
        messages: list[ChatMessage],
        tools: list[ToolDef] | None = None,
        max_tokens: int = 600,
        temperature: float = 0.2,
    ) -> AsyncIterator[ChatChunk]:
        """Stream from primary, falling back to the secondary on failure."""
        kwargs = {
            "model": model,
            "messages": messages,
            "tools": tools,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        # Circuit open → straight to fallback.
        if self.circuit_is_open and self.fallback is not None:
            log.info("llm_router_circuit_open", provider=self.primary.name)
            async for c in self.fallback.stream_chat(**kwargs):
                yield c
            return

        # Try primary; if it fails BEFORE producing chunks, fall through.
        # Once chunks have been emitted to the caller, we cannot retry without
        # corrupting the response — surface the error in that case.
        produced_any = False
        try:
            async for c in self.primary.stream_chat(**kwargs):
                produced_any = True
                yield c
            self._consecutive_failures = 0
            return
        except LLMUnavailable as exc:
            if produced_any:
                # Mid-stream failure — caller has already seen partial output;
                # bubble up rather than silently splicing in a different model.
                self._record_failure()
                log.warning(
                    "llm_router_primary_mid_stream_failure",
                    provider=self.primary.name,
                    error=str(exc),
                )
                raise
            self._record_failure()
            log.warning(
                "llm_router_primary_failed_before_emit",
                provider=self.primary.name,
                error=str(exc),
            )

        if self.fallback is None:
            raise LLMUnavailable(
                f"Primary provider '{self.primary.name}' failed and no fallback is configured.",
            )

        log.info(
            "llm_router_falling_back",
            primary=self.primary.name,
            fallback=self.fallback.name,
        )
        async for c in self.fallback.stream_chat(**kwargs):
            yield c

    def _record_failure(self) -> None:
        self._consecutive_failures += 1
        if self._consecutive_failures >= CONSECUTIVE_FAILURES_TO_OPEN:
            self._circuit_open_until = time.monotonic() + CIRCUIT_OPEN_SECONDS
            log.warning(
                "llm_router_circuit_opened",
                provider=self.primary.name,
                seconds=CIRCUIT_OPEN_SECONDS,
            )
