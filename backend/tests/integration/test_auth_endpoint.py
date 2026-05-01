"""Integration tests for /auth/* and admin gating (P4-01 partial)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.security import get_password_hash

pytestmark = pytest.mark.integration

_TEST_PASSWORD = "test-admin-password-for-integration"


@pytest.fixture(autouse=True)
def _set_admin_password() -> None:
    """Inject a real bcrypt hash so /auth/login can succeed."""
    settings = get_settings()
    settings.ADMIN_PASSWORD_HASH = type(settings.ADMIN_PASSWORD_HASH)(
        get_password_hash(_TEST_PASSWORD)
    )


def test_admin_routes_require_auth(client: TestClient) -> None:
    # Strip any cookies from prior tests so we hit the unauthenticated branch.
    client.cookies.clear()
    r = client.get("/api/v1/admin/predictions")
    assert r.status_code == 401


def test_login_sets_cookie_and_allows_admin_access(client: TestClient) -> None:
    settings = get_settings()
    r = client.post(
        "/api/v1/auth/login",
        json={"username": settings.ADMIN_USERNAME, "password": _TEST_PASSWORD},
    )
    assert r.status_code == 200, r.text
    assert "access_token" in r.cookies

    me = client.get("/api/v1/admin/me")
    assert me.status_code == 200
    assert me.json()["role"] == "admin"


def test_login_wrong_password_401(client: TestClient) -> None:
    client.cookies.clear()
    r = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "wrong"},
    )
    assert r.status_code == 401


def test_logout_clears_cookie(client: TestClient) -> None:
    settings = get_settings()
    client.post(
        "/api/v1/auth/login",
        json={"username": settings.ADMIN_USERNAME, "password": _TEST_PASSWORD},
    )
    r = client.post("/api/v1/auth/logout")
    assert r.status_code == 200
    # Subsequent admin call must fail.
    client.cookies.clear()
    r2 = client.get("/api/v1/admin/me")
    assert r2.status_code == 401
