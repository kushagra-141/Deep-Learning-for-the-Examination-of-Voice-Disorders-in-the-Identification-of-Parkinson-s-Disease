"""Async SQLAlchemy engine + session factory."""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

_settings = get_settings()

# SQLite needs different pool args than PostgreSQL
_engine_kwargs: dict = {
    "future": True,
    "echo": _settings.DEBUG,
}
if not _settings.DATABASE_URL.startswith("sqlite"):
    _engine_kwargs["pool_size"] = _settings.DB_POOL_SIZE
    _engine_kwargs["pool_timeout"] = _settings.DB_POOL_TIMEOUT_S

engine = create_async_engine(_settings.DATABASE_URL, **_engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields a DB session per request."""
    async with AsyncSessionLocal() as session:
        yield session
