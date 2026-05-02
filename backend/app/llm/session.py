"""Ephemeral chat-session store.

Sessions live in Redis with a 24-h TTL when Redis is reachable, falling back
to a process-local LRU dict otherwise (good enough for dev, since chat
sessions are inherently short-lived).
"""
from __future__ import annotations

import asyncio
import json
import time
import uuid
from typing import Any

import structlog

from app.core.config import get_settings
from app.llm.providers import ChatMessage

log = structlog.get_logger(__name__)

SESSION_TTL_SECONDS = 24 * 3600
MAX_HISTORY_MESSAGES = 30  # Drops oldest user/assistant pairs past this cap.


class _MemoryStore:
    def __init__(self) -> None:
        self._sessions: dict[str, tuple[list[dict[str, Any]], float]] = {}
        self._lock = asyncio.Lock()

    async def load(self, sid: str) -> list[dict[str, Any]] | None:
        async with self._lock:
            row = self._sessions.get(sid)
            if row is None:
                return None
            data, expires = row
            if expires <= time.time():
                self._sessions.pop(sid, None)
                return None
            return list(data)

    async def save(self, sid: str, messages: list[dict[str, Any]]) -> None:
        async with self._lock:
            self._sessions[sid] = (messages, time.time() + SESSION_TTL_SECONDS)


class _RedisStore:
    def __init__(self, client: Any) -> None:
        self._r = client

    async def load(self, sid: str) -> list[dict[str, Any]] | None:
        raw = await self._r.get(f"llm:session:{sid}")
        if raw is None:
            return None
        return list(json.loads(raw))

    async def save(self, sid: str, messages: list[dict[str, Any]]) -> None:
        await self._r.setex(
            f"llm:session:{sid}",
            SESSION_TTL_SECONDS,
            json.dumps(messages, ensure_ascii=False),
        )


_store: _MemoryStore | _RedisStore | None = None


async def _get_store() -> _MemoryStore | _RedisStore:
    global _store
    if _store is not None:
        return _store
    settings = get_settings()
    try:
        from redis import asyncio as aioredis  # type: ignore[import-not-found]

        client = aioredis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        await client.ping()
        _store = _RedisStore(client)
    except Exception as exc:  # pragma: no cover — environmental
        log.warning("llm_session_falling_back_to_memory", error=str(exc))
        _store = _MemoryStore()
    return _store


async def load_history(session_id: str) -> list[ChatMessage]:
    store = await _get_store()
    raw = await store.load(session_id)
    if not raw:
        return []
    return [ChatMessage.model_validate(item) for item in raw]


async def save_history(session_id: str, history: list[ChatMessage]) -> None:
    trimmed = history[-MAX_HISTORY_MESSAGES:]
    store = await _get_store()
    await store.save(session_id, [m.model_dump(exclude_none=True) for m in trimmed])


def new_session_id() -> str:
    return uuid.uuid4().hex


async def reset() -> None:  # for tests
    global _store
    _store = None
