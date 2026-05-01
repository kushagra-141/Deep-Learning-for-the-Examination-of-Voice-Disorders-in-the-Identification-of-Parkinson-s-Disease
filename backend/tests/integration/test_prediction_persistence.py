"""Integration tests for prediction + feedback + admin persistence (P1-13)."""
from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.security import get_password_hash

pytestmark = pytest.mark.integration

_TEST_PASSWORD = "test-admin-password-for-integration"


@pytest.fixture
def admin_login(client: TestClient) -> None:
    """Configure admin password and log in. Cookie persists on the client."""
    settings = get_settings()
    settings.ADMIN_PASSWORD_HASH = type(settings.ADMIN_PASSWORD_HASH)(
        get_password_hash(_TEST_PASSWORD)
    )
    r = client.post(
        "/api/v1/auth/login",
        json={"username": settings.ADMIN_USERNAME, "password": _TEST_PASSWORD},
    )
    assert r.status_code == 200, r.text


def _post_prediction(client: TestClient) -> dict:
    sample = client.get("/api/v1/predict/sample?label=1").json()
    r = client.post("/api/v1/predict/", json={"features": sample})
    assert r.status_code == 200, r.text
    return r.json()


def test_predict_persists_and_returns_uuid(client: TestClient) -> None:
    body = _post_prediction(client)
    # The id must be a real UUID (mint by DB), not a placeholder.
    parsed = uuid.UUID(body["prediction_id"])
    assert parsed.version == 4


def test_feedback_for_unknown_prediction_404(client: TestClient) -> None:
    r = client.post(
        "/api/v1/feedback/",
        json={"prediction_id": str(uuid.uuid4()), "rating": 5},
    )
    assert r.status_code == 404


def test_feedback_for_existing_prediction_persists(client: TestClient) -> None:
    body = _post_prediction(client)
    r = client.post(
        "/api/v1/feedback/",
        json={"prediction_id": body["prediction_id"], "rating": 4, "comment": "ok"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["received"] is True
    uuid.UUID(r.json()["feedback_id"])


def test_admin_predictions_lists_persisted_rows(
    client: TestClient, admin_login: None
) -> None:
    body = _post_prediction(client)
    r = client.get("/api/v1/admin/predictions?limit=5")
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) >= 1
    assert any(item["id"] == body["prediction_id"] for item in items)
    # First item is most recent — model_count must be > 0.
    assert items[0]["model_count"] >= 1


def test_admin_feedback_lists_persisted_rows(
    client: TestClient, admin_login: None
) -> None:
    body = _post_prediction(client)
    client.post(
        "/api/v1/feedback/",
        json={"prediction_id": body["prediction_id"], "rating": 3},
    )
    r = client.get("/api/v1/admin/feedback?limit=5")
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) >= 1
    assert any(item["prediction_id"] == body["prediction_id"] for item in items)


def test_admin_pagination_invalid_cursor_400(
    client: TestClient, admin_login: None
) -> None:
    r = client.get("/api/v1/admin/predictions?cursor=not-a-date")
    assert r.status_code == 400
