"""Integration tests for /models/* (P1-10)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration

EXPECTED_MODELS = {
    "knn", "svm", "decision_tree", "bagging", "lightgbm",
    "adaboost", "random_forest", "xgboost", "pca_rf",
}


def test_list_models(client: TestClient) -> None:
    r = client.get("/api/v1/models")
    assert r.status_code == 200
    names = {m["name"] for m in r.json()}
    assert EXPECTED_MODELS <= names


def test_compare_models(client: TestClient) -> None:
    r = client.get("/api/v1/models/compare")
    assert r.status_code == 200
    assert len(r.json()["models"]) >= len(EXPECTED_MODELS)


def test_confusion_matrix_for_each_model(client: TestClient) -> None:
    for name in EXPECTED_MODELS:
        r = client.get(f"/api/v1/models/{name}/confusion-matrix")
        assert r.status_code == 200, f"{name}: {r.text}"
        body = r.json()
        assert {"tn", "fp", "fn", "tp", "labels"} <= set(body.keys())


def test_confusion_matrix_unknown_model_404(client: TestClient) -> None:
    r = client.get("/api/v1/models/not_a_real_model/confusion-matrix")
    assert r.status_code == 404


@pytest.mark.parametrize("name", ["lightgbm", "random_forest", "knn"])
def test_roc_returns_curve(client: TestClient, name: str) -> None:
    r = client.get(f"/api/v1/models/{name}/roc")
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["fpr"]) == len(body["tpr"]) >= 2
    assert body["fpr"][0] == 0.0
    assert body["tpr"][-1] == 1.0


@pytest.mark.parametrize("name", ["lightgbm", "random_forest"])
def test_pr_returns_curve(client: TestClient, name: str) -> None:
    r = client.get(f"/api/v1/models/{name}/pr")
    assert r.status_code == 200
    body = r.json()
    assert len(body["precision"]) == len(body["recall"]) >= 2


def test_calibration_validates_n_bins(client: TestClient) -> None:
    r = client.get("/api/v1/models/lightgbm/calibration?n_bins=2")
    assert r.status_code == 400
    r = client.get("/api/v1/models/lightgbm/calibration?n_bins=10")
    assert r.status_code == 200
