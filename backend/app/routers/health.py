"""Health check endpoint."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/healthz")
async def healthz() -> dict:
    """Basic health check for load balancers."""
    return {"status": "ok"}
