"""P1-08: FastAPI application factory."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging
from app.core.observability import init_observability, instrument_app
from app.core.rate_limit import limiter, rate_limit_handler
from app.ml.manager import ModelManager
from app.routers import (
    admin,
    analytics,
    audio,
    auth,
    batch,
    chat,
    explain,
    feedback,
    health,
    help as help_router,
    models,
    predict,
    predictions,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    settings = get_settings()
    configure_logging(settings)
    init_observability(settings)

    # Load ML models into memory
    app.state.model_manager = ModelManager.from_dir(settings.MODELS_DIR)
    # app.state.model_manager.verify_integrity()  # Temporarily disabled until models are trained

    yield
    # Graceful shutdown hooks here


def create_app() -> FastAPI:
    """FastAPI application factory."""
    settings = get_settings()
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        docs_url=f"{settings.API_PREFIX}/docs",
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        lifespan=lifespan,
    )

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(*rate_limit_handler())

    # Error handling
    register_error_handlers(app)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.PUBLIC_BASE_URL],
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )

    # Security Headers
    @app.middleware("http")
    async def security_headers_middleware(request: Request, call_next):
        response = await call_next(request)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response

    # Observability
    instrument_app(app)

    # Routers
    p = settings.API_PREFIX
    app.include_router(health.router, prefix=p, tags=["health"])
    app.include_router(predict.router, prefix=f"{p}/predict", tags=["predict"])
    app.include_router(audio.router, prefix=f"{p}/audio", tags=["audio"])
    app.include_router(batch.router, prefix=f"{p}/batch", tags=["batch"])
    app.include_router(models.router, prefix=p, tags=["models"])
    app.include_router(analytics.router, prefix=f"{p}/analytics", tags=["analytics"])
    app.include_router(feedback.router, prefix=f"{p}/feedback", tags=["feedback"])
    app.include_router(auth.router, prefix=f"{p}/auth", tags=["auth"])
    app.include_router(admin.router, prefix=f"{p}/admin", tags=["admin"])
    app.include_router(explain.router, prefix=f"{p}/explain", tags=["explain"])
    app.include_router(chat.router, prefix=f"{p}/chat", tags=["llm-chat"])
    app.include_router(help_router.router, prefix=f"{p}/help", tags=["llm-help"])
    app.include_router(predictions.router, prefix=f"{p}/predictions", tags=["llm-narrate"])

    return app


app = create_app()
