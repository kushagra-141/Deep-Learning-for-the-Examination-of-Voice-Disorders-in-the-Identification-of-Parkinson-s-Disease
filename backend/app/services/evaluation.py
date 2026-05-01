"""P1-06: Model evaluation — per-model metrics and cross-validation."""
from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_score


def compute_metrics(estimator: Any, X_test: np.ndarray, y_test: np.ndarray) -> dict:
    """Compute classification metrics on a held-out test set."""
    y_pred = estimator.predict(X_test)
    y_proba = estimator.predict_proba(X_test)[:, 1]
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    return {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, y_proba)),
        "confusion_matrix": {
            "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
        },
    }


def cv_score(
    estimator: Any,
    X: np.ndarray,
    y: np.ndarray,
    *,
    k: int = 5,
    seed: int = 1,
) -> dict:
    """Stratified K-fold cross-validation accuracy."""
    cv = StratifiedKFold(n_splits=k, shuffle=True, random_state=seed)
    scores = cross_val_score(estimator, X, y, cv=cv, scoring="accuracy", n_jobs=-1)
    return {
        "cv_accuracy_mean": float(scores.mean()),
        "cv_accuracy_std": float(scores.std()),
    }
