"""P1-08 + P4-03: Rate limiting via slowapi.

The limiter is auto-disabled when `ENV=test` so the integration suite isn't
forced to thread sleeps / tokens through every test. Production and dev keep
real per-IP enforcement (Redis-backed when `REDIS_URL` is set on the limiter
instance — left to a Phase 4 wiring change).
"""
from __future__ import annotations

from typing import Callable

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import get_settings

_settings = get_settings()

limiter = Limiter(
    key_func=get_remote_address,
    enabled=_settings.ENV != "test",
)


def rate_limit_handler() -> tuple[type[Exception], Callable]:
    """Return the exception and handler for FastAPI."""
    return RateLimitExceeded, _rate_limit_exceeded_handler
