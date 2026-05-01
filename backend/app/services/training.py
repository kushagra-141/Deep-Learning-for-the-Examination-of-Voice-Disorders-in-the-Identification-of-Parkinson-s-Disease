"""P1-06: Trainer functions for all 9 model families + calibration.

Each trainer accepts (X_train_scaled, y_train, *, seed=1) and returns a
fitted estimator (or dict for pca_rf). All trainers use class_weight="balanced"
where supported to handle the 75/25 class imbalance in the UCI dataset.
"""
from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.calibration import CalibratedClassifierCV


# ── Individual trainers ───────────────────────────────────────────────────────

def train_knn(X: np.ndarray, y: np.ndarray, *, seed: int = 1) -> Any:
    from sklearn.neighbors import KNeighborsClassifier
    return KNeighborsClassifier(n_neighbors=5).fit(X, y)


def train_svm(X: np.ndarray, y: np.ndarray, *, seed: int = 1) -> Any:
    from sklearn.svm import SVC
    # probability=True needed for calibration; class_weight handles imbalance
    return SVC(
        kernel="linear",
        probability=True,
        class_weight="balanced",
        random_state=seed,
    ).fit(X, y)


def train_decision_tree(X: np.ndarray, y: np.ndarray, *, seed: int = 1) -> Any:
    from sklearn.tree import DecisionTreeClassifier
    return DecisionTreeClassifier(
        max_depth=2, class_weight="balanced", random_state=seed
    ).fit(X, y)


def train_bagging(X: np.ndarray, y: np.ndarray, *, seed: int = 1) -> Any:
    from sklearn.ensemble import BaggingClassifier
    from sklearn.tree import DecisionTreeClassifier
    base = DecisionTreeClassifier(max_depth=6, random_state=seed)
    return BaggingClassifier(
        estimator=base, n_estimators=300, n_jobs=-1, random_state=seed
    ).fit(X, y)


def train_lightgbm(X: np.ndarray, y: np.ndarray, *, seed: int = 1) -> Any:
    from lightgbm import LGBMClassifier
    return LGBMClassifier(
        random_state=seed, class_weight="balanced", verbosity=-1
    ).fit(X, y)


def train_adaboost(X: np.ndarray, y: np.ndarray, *, seed: int = 1) -> Any:
    from sklearn.ensemble import AdaBoostClassifier
    return AdaBoostClassifier(n_estimators=50, random_state=seed).fit(X, y)


def train_random_forest(X: np.ndarray, y: np.ndarray, *, seed: int = 1) -> Any:
    from sklearn.ensemble import RandomForestClassifier
    return RandomForestClassifier(
        n_estimators=30,
        criterion="entropy",
        class_weight="balanced",
        random_state=seed,
        n_jobs=-1,
    ).fit(X, y)


def train_xgboost(X: np.ndarray, y: np.ndarray, *, seed: int = 1) -> Any:
    from xgboost import XGBClassifier
    return XGBClassifier(
        random_state=seed, eval_metric="logloss", n_jobs=-1
    ).fit(X, y)


def train_pca_rf(X: np.ndarray, y: np.ndarray, *, seed: int = 1) -> dict[str, Any]:
    """Returns dict with 'pca' and 'rf' keys (stored separately in models/)."""
    from sklearn.decomposition import PCA
    from sklearn.ensemble import RandomForestClassifier

    pca = PCA(n_components=9, random_state=seed).fit(X)
    X_pca = pca.transform(X)
    rf = RandomForestClassifier(
        n_estimators=30,
        criterion="entropy",
        class_weight="balanced",
        random_state=seed,
        n_jobs=-1,
    ).fit(X_pca, y)
    return {"pca": pca, "rf": rf}


# ── Calibration ───────────────────────────────────────────────────────────────

#: Models whose predict_proba output needs isotonic calibration (ADR-0011)
NEEDS_CALIBRATION = {"knn", "svm", "decision_tree"}


def calibrate(estimator: Any, X_train: np.ndarray, y_train: np.ndarray) -> Any:
    """Wrap estimator in CalibratedClassifierCV(isotonic, cv=5), fit on training set."""
    cal = CalibratedClassifierCV(estimator=estimator, method="isotonic", cv=5)
    cal.fit(X_train, y_train)
    return cal


# ── Registry of all trainers ──────────────────────────────────────────────────

TRAINERS: dict[str, Any] = {
    "knn": train_knn,
    "svm": train_svm,
    "decision_tree": train_decision_tree,
    "bagging": train_bagging,
    "lightgbm": train_lightgbm,
    "adaboost": train_adaboost,
    "random_forest": train_random_forest,
    "xgboost": train_xgboost,
    "pca_rf": train_pca_rf,
}
