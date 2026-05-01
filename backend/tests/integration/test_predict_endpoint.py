"""Integration tests for /predict (P1-09)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.schemas.feature import VoiceFeatures

pytestmark = pytest.mark.integration


def test_predict_sample_default_random(client: TestClient) -> None:
    r = client.get("/api/v1/predict/sample")
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body.keys()) == set(VoiceFeatures.FEATURE_ORDER)


@pytest.mark.parametrize("label", ["0", "1"])
def test_predict_sample_by_label(client: TestClient, label: str) -> None:
    r = client.get(f"/api/v1/predict/sample?label={label}")
    assert r.status_code == 200
    body = r.json()
    # Round-trip through the schema to confirm it's a valid payload.
    VoiceFeatures.model_validate(body)


def test_predict_sample_invalid_label_422(client: TestClient) -> None:
    r = client.get("/api/v1/predict/sample?label=banana")
    assert r.status_code == 422


def test_post_predict_with_sample_payload(client: TestClient) -> None:
    sample = client.get("/api/v1/predict/sample?label=1").json()
    r = client.post("/api/v1/predict/", json={"features": sample})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["input_mode"] == "manual"
    assert body["ensemble"]["model_name"] == "ensemble"
    assert 0.0 <= body["ensemble"]["probability"] <= 1.0
    assert len(body["per_model"]) >= 1
