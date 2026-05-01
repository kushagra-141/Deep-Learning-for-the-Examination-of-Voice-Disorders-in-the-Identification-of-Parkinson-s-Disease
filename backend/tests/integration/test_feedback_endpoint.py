"""Integration tests for /feedback (P1-09 partial)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def test_feedback_happy_path(client: TestClient) -> None:
    r = client.post(
        "/api/v1/feedback/",
        json={"prediction_id": "abc-123", "rating": 5, "comment": "Looks good"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["received"] is True
    assert body["feedback_id"]


def test_feedback_rating_out_of_range(client: TestClient) -> None:
    r = client.post("/api/v1/feedback/", json={"prediction_id": "x", "rating": 6})
    assert r.status_code == 422
