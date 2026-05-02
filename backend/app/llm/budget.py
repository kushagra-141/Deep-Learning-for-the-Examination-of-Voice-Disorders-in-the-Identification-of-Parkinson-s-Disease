"""P3.5-06: Per-IP daily token bucket + global ceiling.

Backed by Redis when ``REDIS_URL`` is reachable; falls back to a process-local
in-memory store otherwise (so dev / tests don't require Redis).
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol

import structlog

from app.core.config import get_settings

log = structlog.get_logger(__name__)


class BudgetExceeded(Exception):
    """Raised when the per-IP or global daily token cap is hit."""

    def __init__(self, scope: str, retry_after_seconds: int) -> None:
        super().__init__(f"LLM token budget exceeded ({scope})")
        self.scope = scope
        self.retry_after_seconds = retry_after_seconds


# ── Backends ────────────────────────────────────────────────────────────────


class _Backend(Protocol):
    async def incr(self, key: str, amount: int, ttl_seconds: int) -> int: ...
    async def get(self, key: str) -> int: ...


class _InMemoryBackend:
    """Process-local fallback. NOT shared across workers — fine for dev only."""

    def __init__(self) -> None:
        self._counters: dict[str, tuple[int, float]] = {}
        self._lock = asyncio.Lock()

    async def incr(self, key: str, amount: int, ttl_seconds: int) -> int:
        async with self._lock:
            now = time.time()
            value, expires = self._counters.get(key, (0, 0.0))
            if expires <= now:
                value = 0
                expires = now + ttl_seconds
            value += amount
            self._counters[key] = (value, expires)
            return value

    async def get(self, key: str) -> int:
        async with self._lock:
            value, expires = self._counters.get(key, (0, 0.0))
            if expires <= time.time():
                return 0
            return value


class _RedisBackend:
    def __init__(self, client: Any) -> None:
        self._r = client

    async def incr(self, key: str, amount: int, ttl_seconds: int) -> int:
        new_value = int(await self._r.incrby(key, amount))
        if new_value == amount:
            await self._r.expire(key, ttl_seconds)
        return new_value

    async def get(self, key: str) -> int:
        value = await self._r.get(key)
        if value is None:
            return 0
        return int(value)


_backend: _Backend | None = None


async def _get_backend() -> _Backend:
    """Lazily build the backend, preferring Redis when reachable."""
    global _backend
    if _backend is not None:
        return _backend
    settings = get_settings()
    try:
        # Late import — keeps redis dep optional in tests / sqlite-only setups.
        from redis import asyncio as aioredis  # type: ignore[import-not-found]

        client = aioredis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        # Probe: `ping` raises if the server isn't there.
        await client.ping()
        _backend = _RedisBackend(client)
        log.info("llm_budget_backend", backend="redis")
    except Exception as exc:  # pragma: no cover — environmental
        log.warning("llm_budget_falling_back_to_memory", error=str(exc))
        _backend = _InMemoryBackend()
    return _backend


# ── API ─────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class BudgetCheck:
    """Result of a budget probe — no side effects on the counter."""

    used_tokens: int
    limit: int
    remaining: int


def _today_key(client_fp: str) -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"llm:tokens:{client_fp}:{today}"


def _global_today_key() -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"llm:tokens:global:{today}"


def _seconds_until_utc_midnight() -> int:
    now = datetime.now(timezone.utc)
    tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if tomorrow <= now:
        # Add 24h via timestamps to avoid month/year wraparound bugs.
        tomorrow = datetime.fromtimestamp(now.timestamp() + 86400, tz=timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0,
        )
    return max(60, int((tomorrow - now).total_seconds()))


async def assert_budget(client_fp: str) -> None:
    """Raise :class:`BudgetExceeded` if the IP or global cap is already met."""
    settings = get_settings()
    limit = settings.LLM_DAILY_TOKEN_BUDGET
    backend = await _get_backend()

    used = await backend.get(_today_key(client_fp))
    if used >= limit:
        raise BudgetExceeded("ip", _seconds_until_utc_midnight())

    global_used = await backend.get(_global_today_key())
    # Global ceiling = 50× per-IP budget — protects free quotas overall.
    global_limit = limit * 50
    if global_used >= global_limit:
        raise BudgetExceeded("global", _seconds_until_utc_midnight())


async def commit_tokens(client_fp: str, tokens: int) -> int:
    """Charge ``tokens`` against both the per-IP and global counters.

    Returns the new per-IP counter value (mostly for tests / metrics).
    """
    if tokens <= 0:
        return 0
    backend = await _get_backend()
    ttl = _seconds_until_utc_midnight()
    new_ip = await backend.incr(_today_key(client_fp), tokens, ttl)
    await backend.incr(_global_today_key(), tokens, ttl)
    return new_ip


async def reset() -> None:
    """For tests."""
    global _backend
    _backend = None
