"""SHAP wiring tests (P1-12)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.schemas.feature import VoiceFeatures

pytestmark = pytest.mark.integration


def _post_predict(client: TestClient) -> dict:
    sample = client.get("/api/v1/predict/sample?label=1").json()
    r = client.post("/api/v1/predict/", json={"features": sample})
    assert r.status_code == 200, r.text
    return r.json()


def test_ensemble_shap_top_present(client: TestClient) -> None:
    body = _post_predict(client)
    shap = body["ensemble"]["shap_top"]
    assert shap is not None and len(shap) == 5
    for row in shap:
        assert {"feature", "value", "shap"} == set(row.keys())
        assert row["feature"] in VoiceFeatures.FEATURE_ORDER
        assert isinstance(row["value"], (int, float))
        assert isinstance(row["shap"], (int, float))


def test_shap_sorted_by_abs_magnitude(client: TestClient) -> None:
    body = _post_predict(client)
    shap = body["ensemble"]["shap_top"]
    abs_vals = [abs(r["shap"]) for r in shap]
    assert abs_vals == sorted(abs_vals, reverse=True)


def test_primary_model_carries_same_shap(client: TestClient) -> None:
    """Whatever the primary model is, its per-model entry mirrors the ensemble."""
    body = _post_predict(client)
    primary = body["primary_model"]
    assert primary != "ensemble", "primary_model should name a real classifier"

    primary_entry = next((m for m in body["per_model"] if m["model_name"] == primary), None)
    assert primary_entry is not None
    assert primary_entry["shap_top"] == body["ensemble"]["shap_top"]


def test_other_models_have_no_shap(client: TestClient) -> None:
    """Only the primary's per-model entry carries SHAP — others stay null."""
    body = _post_predict(client)
    primary = body["primary_model"]
    for m in body["per_model"]:
        if m["model_name"] != primary:
            assert m["shap_top"] is None
