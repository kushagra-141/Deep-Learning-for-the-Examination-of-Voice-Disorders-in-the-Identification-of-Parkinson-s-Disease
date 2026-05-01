"""P1-12: SHAP wrappers per model family.

Returns the top-k features by `|shap|` for a single prediction. The cost of
constructing a `TreeExplainer` dwarfs the per-call compute, so explainer
instances are cached by model_name (each model is loaded exactly once at
process start by `ModelManager`).

SVM/KNN paths would need `KernelExplainer` + a stored background sample —
that's deferred until P3.5/Phase 4. Failures never break the prediction
flow: `compute_shap_top_k` returns `None` and the response just omits SHAP.
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np

log = logging.getLogger(__name__)

#: Models for which `shap.TreeExplainer` works out-of-the-box.
_TREE_EXPLAINABLE: frozenset[str] = frozenset(
    {"random_forest", "xgboost", "lightgbm", "decision_tree", "adaboost", "bagging"}
)

#: TreeExplainer instances, keyed by model_name. Populated lazily.
_explainer_cache: dict[str, Any] = {}


def _get_tree_explainer(model_name: str, model: Any) -> Any | None:
    """Return a cached `shap.TreeExplainer`, or None if unavailable."""
    if model_name in _explainer_cache:
        return _explainer_cache[model_name]
    try:
        import shap
    except ImportError:
        return None
    try:
        explainer = shap.TreeExplainer(model)
    except Exception as exc:  # noqa: BLE001 — log and gracefully skip
        log.warning("shap_explainer_init_failed", extra={"model": model_name, "err": str(exc)})
        return None
    _explainer_cache[model_name] = explainer
    return explainer


def _shap_class1(shap_values: Any) -> np.ndarray:
    """Extract the class=1 SHAP vector from any TreeExplainer output shape."""
    arr = np.asarray(shap_values)
    # (n_samples, n_features, n_classes)
    if arr.ndim == 3:
        return arr[0, :, 1]
    # list of (n_samples, n_features) per class — older shap API
    if isinstance(shap_values, list):
        return np.asarray(shap_values[1])[0]
    # (n_samples, n_features) — binary, single output
    if arr.ndim == 2:
        return arr[0]
    # (n_features,) — already squeezed
    return arr


def compute_shap_top_k(
    model: Any,
    model_name: str,
    scaled_features: list[float],
    original_values: list[float],
    feature_names: list[str],
    *,
    k: int = 5,
) -> list[dict[str, Any]] | None:
    """Compute top-k SHAP contributions for a single sample.

    `scaled_features` is what the model sees (post-StandardScaler); `original_values`
    is what the user submitted and what we want to display. SHAP magnitudes live
    in scaled space — this is correct given the model was trained on scaled data.

    Returns `[{feature, value, shap}]` sorted by `|shap|` desc, or `None` on failure.
    """
    if model_name not in _TREE_EXPLAINABLE:
        return None
    explainer = _get_tree_explainer(model_name, model)
    if explainer is None:
        return None

    try:
        X = np.array([scaled_features], dtype=float)
        raw = explainer.shap_values(X)
        sv = _shap_class1(raw)
        if len(sv) != len(feature_names):
            log.warning(
                "shap_shape_mismatch",
                extra={"model": model_name, "got": len(sv), "want": len(feature_names)},
            )
            return None

        rows = [
            {"feature": name, "value": float(orig), "shap": float(s)}
            for name, orig, s in zip(feature_names, original_values, sv, strict=True)
        ]
        rows.sort(key=lambda r: abs(r["shap"]), reverse=True)
        return rows[:k]
    except Exception as exc:  # noqa: BLE001 — never break the prediction flow
        log.warning("shap_compute_failed", extra={"model": model_name, "err": str(exc)})
        return None
