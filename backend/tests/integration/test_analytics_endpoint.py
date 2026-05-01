"""Integration tests for /analytics/* (P1-11)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def test_dataset_stats(client: TestClient) -> None:
    r = client.get("/api/v1/analytics/dataset-stats")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] == 195  # UCI Parkinson's dataset has 195 rows
    assert body["feature_count"] == 22
    assert body["by_class"]["healthy"] + body["by_class"]["parkinsons"] == 195
    assert 0 < body["class_balance_pct"] <= 100


def test_feature_distribution_known_feature(client: TestClient) -> None:
    r = client.get("/api/v1/analytics/feature/MDVP:Fo(Hz)?bins=20")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["feature"] == "MDVP:Fo(Hz)"
    assert len(body["counts"]) == 20
    assert len(body["bins"]) == 21  # bin edges = counts+1
    assert {"healthy", "parkinsons"} == set(body["by_class"].keys())


def test_feature_distribution_unknown_feature_404(client: TestClient) -> None:
    r = client.get("/api/v1/analytics/feature/not_a_real_feature")
    assert r.status_code == 404


def test_correlation_matrix_shape(client: TestClient) -> None:
    r = client.get("/api/v1/analytics/correlation")
    assert r.status_code == 200
    body = r.json()
    assert len(body["features"]) == 22
    assert len(body["matrix"]) == 22
    assert all(len(row) == 22 for row in body["matrix"])
    # Diagonal should be 1.0 (self-correlation)
    for i in range(22):
        assert abs(body["matrix"][i][i] - 1.0) < 1e-6


def test_pca_projection(client: TestClient) -> None:
    r = client.get("/api/v1/analytics/pca?components=2")
    assert r.status_code == 200
    body = r.json()
    assert body["components"] == 2
    assert len(body["explained_variance"]) == 2
    assert len(body["points"]) == 195
    for p in body["points"][:5]:
        assert {"x", "y", "label"} <= set(p.keys())
        assert p["label"] in (0, 1)
