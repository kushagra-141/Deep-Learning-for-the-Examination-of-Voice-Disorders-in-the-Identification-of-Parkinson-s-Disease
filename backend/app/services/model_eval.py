"""P1-10: Per-model curve computation (ROC, PR, calibration).

The model artifacts on disk only carry summary metrics in `manifest.json`.
For curves we re-run inference against the same held-out test split that was
used at training time (seed=42 — see `scripts/train.py`).

Results are cached in-process — the bundled dataset is deterministic, so this
is a one-shot cost per model + curve type.
"""
from __future__ import annotations

import warnings
from functools import lru_cache
from typing import Any

import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import precision_recall_curve, roc_curve

from app.core.config import get_settings
from app.ml.manager import ModelManager
from app.schemas.feature import VoiceFeatures
from app.services.preprocessing import (
    fit_scaler,
    load_dataset,
    split_xy,
    train_test_split_xy,
)

# Same seed used in scripts/train.py — must match for the test split to be
# the same one the manifest metrics were computed against.
_TRAIN_SEED = 42

# LightGBM was trained with a DataFrame, so it expects feature names at
# inference. Other sklearn models were trained on a raw numpy array.
_NEEDS_DF: set[str] = {"lightgbm"}


@lru_cache(maxsize=1)
def _holdout() -> tuple[np.ndarray, np.ndarray]:
    """Return (X_test_scaled, y_test) using the same split as training."""
    settings = get_settings()
    df = load_dataset(settings.DATA_DIR / "parkinsons.data")
    X, y = split_xy(df)
    X_train, X_test, _, y_test = train_test_split_xy(X, y, seed=_TRAIN_SEED)
    scaler = fit_scaler(X_train)
    return scaler.transform(X_test), y_test


def _proba(manager: ModelManager, name: str, X_scaled: np.ndarray) -> np.ndarray:
    """Return P(class=1) for every row of X_scaled for the named model."""
    bundle = manager.get_model(name)
    model = bundle["model"]
    calibrator = bundle.get("calibrator")

    if name in _NEEDS_DF:
        X_in: Any = pd.DataFrame(X_scaled, columns=VoiceFeatures.FEATURE_ORDER)
    elif name == "pca_rf":
        # The on-disk pca_rf is the RF; the matching PCA was saved separately.
        from pathlib import Path

        import joblib

        pca_path: Path = manager.models_dir / "pca.joblib"
        pca = joblib.load(pca_path)
        X_in = pca.transform(X_scaled)
    else:
        X_in = X_scaled

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if calibrator is not None and hasattr(calibrator, "predict_proba"):
            return calibrator.predict_proba(X_in)[:, 1]
        if hasattr(model, "predict_proba"):
            return model.predict_proba(X_in)[:, 1]
        if hasattr(model, "decision_function"):
            dec = model.decision_function(X_in)
            return 1.0 / (1.0 + np.exp(-dec))
        # Last-resort: hard label as probability
        return model.predict(X_in).astype(float)


def get_confusion_matrix(manager: ModelManager, name: str) -> dict:
    """Read the cached confusion matrix from the manifest."""
    if manager.manifest is None:
        raise RuntimeError("Manifest not loaded")
    for entry in manager.manifest["models"]:
        if entry["name"] == name:
            cm = entry["metrics"]["confusion_matrix"]
            return {**cm, "labels": ["healthy", "parkinsons"]}
    raise KeyError(name)


def get_roc(manager: ModelManager, name: str) -> dict:
    X_test, y_test = _holdout()
    proba = _proba(manager, name, X_test)
    fpr, tpr, thresholds = roc_curve(y_test, proba)
    return {
        "model": name,
        "fpr": [float(v) for v in fpr.tolist()],
        "tpr": [float(v) for v in tpr.tolist()],
        "thresholds": [float(v) for v in thresholds.tolist()],
    }


def get_pr(manager: ModelManager, name: str) -> dict:
    X_test, y_test = _holdout()
    proba = _proba(manager, name, X_test)
    precision, recall, thresholds = precision_recall_curve(y_test, proba)
    # precision_recall_curve returns thresholds of length n-1; pad to align.
    return {
        "model": name,
        "precision": [float(v) for v in precision.tolist()],
        "recall": [float(v) for v in recall.tolist()],
        "thresholds": [float(v) for v in thresholds.tolist()],
    }


def get_calibration(manager: ModelManager, name: str, *, n_bins: int = 10) -> dict:
    X_test, y_test = _holdout()
    proba = _proba(manager, name, X_test)
    fraction_positives, mean_predicted = calibration_curve(
        y_test, proba, n_bins=n_bins, strategy="uniform"
    )
    return {
        "model": name,
        "mean_predicted_probability": [float(v) for v in mean_predicted.tolist()],
        "fraction_of_positives": [float(v) for v in fraction_positives.tolist()],
        "n_bins": n_bins,
    }
