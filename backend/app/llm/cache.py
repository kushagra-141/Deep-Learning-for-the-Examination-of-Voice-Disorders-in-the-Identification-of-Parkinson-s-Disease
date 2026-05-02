"""P3.5-06: Response cache for tool-free LLM turns.

Key = sha256 of (feature || model || system prompt version || messages JSON).
Value = full assistant text. TTL = 1 h.

Cache only turns where the LLM did NOT call any tools — otherwise a stale
response could mask live what-if simulations.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import time
from typing import Any, Protocol

import structlog

from app.core.config import get_settings

log = structlog.get_logger(__name__)

DEFAULT_TTL_SECONDS = 3600
PROMPT_VERSION = "v1"


class _Backend(Protocol):
    async def get(self, key: str) -> str | None: ...
    async def setex(self, key: str, ttl_seconds: int, value: str) -> None: ...


class _InMemoryBackend:
    def __init__(self) -> None:
        self._store: dict[str, tuple[str, float]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> str | None:
        async with self._lock:
            value_expires = self._store.get(key)
            if value_expires is None:
                return None
            value, expires = value_expires
            if expires <= time.time():
                self._store.pop(key, None)
                return None
            return value

    async def setex(self, key: str, ttl_seconds: int, value: str) -> None:
        async with self._lock:
            self._store[key] = (value, time.time() + ttl_seconds)


class _RedisBackend:
    def __init__(self, client: Any) -> None:
        self._r = client

    async def get(self, key: str) -> str | None:
        value = await self._r.get(key)
        return value if value is not None else None

    async def setex(self, key: str, ttl_seconds: int, value: str) -> None:
        await self._r.setex(key, ttl_seconds, value)


_backend: _Backend | None = None


async def _get_backend() -> _Backend:
    global _backend
    if _backend is not None:
        return _backend
    settings = get_settings()
    try:
        from redis import asyncio as aioredis  # type: ignore[import-not-found]

        client = aioredis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        await client.ping()
        _backend = _RedisBackend(client)
        log.info("llm_cache_backend", backend="redis")
    except Exception as exc:  # pragma: no cover — environmental
        log.warning("llm_cache_falling_back_to_memory", error=str(exc))
        _backend = _InMemoryBackend()
    return _backend


def make_key(*, feature: str, model: str, messages: list[dict[str, Any]]) -> str:
    """Stable hash for the cache key. Pure function — safe to call without I/O."""
    payload = json.dumps(
        {"feat": feature, "model": model, "v": PROMPT_VERSION, "msgs": messages},
        sort_keys=True,
        ensure_ascii=False,
    ).encode("utf-8")
    return "llm:cache:" + hashlib.sha256(payload).hexdigest()


async def lookup(key: str) -> str | None:
    backend = await _get_backend()
    try:
        return await backend.get(key)
    except Exception as exc:  # pragma: no cover
        log.warning("llm_cache_lookup_failed", error=str(exc))
        return None


async def store(key: str, value: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
    if not value:
        return
    backend = await _get_backend()
    try:
        await backend.setex(key, ttl_seconds, value)
    except Exception as exc:  # pragma: no cover
        log.warning("llm_cache_store_failed", error=str(exc))


async def reset() -> None:
    """For tests."""
    global _backend
    _backend = None
