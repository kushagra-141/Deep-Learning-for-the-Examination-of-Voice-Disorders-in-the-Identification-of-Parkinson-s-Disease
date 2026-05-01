"""Global HTTP error handlers and AppException."""
from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class AppException(Exception):
    """Base application exception with HTTP status + machine-readable code."""

    def __init__(
        self,
        *,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        code: str = "INTERNAL_ERROR",
        message: str = "An unexpected error occurred.",
        details: object = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


def _error_payload(request: Request, code: str, message: str, details: object = None) -> dict:
    import structlog

    log = structlog.get_logger()
    request_id = getattr(request.state, "request_id", "unknown")
    log.warning("http_error", code=code, message=message, request_id=request_id)
    payload: dict = {"error": {"code": code, "message": message, "request_id": request_id}}
    if details is not None:
        payload["error"]["details"] = details
    return payload


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(request, exc.code, exc.message, exc.details),
        )

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content=_error_payload(request, "NOT_FOUND", f"Resource not found: {request.url.path}"),
        )

    @app.exception_handler(500)
    async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=_error_payload(request, "INTERNAL_ERROR", "An unexpected error occurred."),
        )
