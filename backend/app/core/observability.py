"""P1-08: Observability (Sentry, Prometheus, OpenTelemetry)."""
from __future__ import annotations

from typing import TYPE_CHECKING

import sentry_sdk
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

if TYPE_CHECKING:
    from app.core.config import Settings


def init_observability(settings: "Settings") -> None:
    """Initialize Sentry if configured."""
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN.get_secret_value(),
            environment=settings.ENV,
            traces_sample_rate=1.0 if settings.ENV == "dev" else 0.1,
        )


def instrument_app(app: FastAPI) -> None:
    """Instrument FastAPI with Prometheus."""
    # We can add OpenTelemetry later
    Instrumentator().instrument(app).expose(app, endpoint="/metrics")
