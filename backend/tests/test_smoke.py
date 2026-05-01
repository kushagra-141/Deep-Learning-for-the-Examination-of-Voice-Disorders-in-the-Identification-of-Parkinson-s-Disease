"""Smoke test — Phase 0 acceptance criterion.

Verifies that the FastAPI stub boots and the root endpoint returns 200.
"""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_root_returns_200() -> None:
    """GET / should return 200 and a non-empty JSON body."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"hello": "world"}


@pytest.mark.asyncio
async def test_healthz_returns_ok() -> None:
    """GET /api/v1/healthz should return 200 {status: ok}."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
