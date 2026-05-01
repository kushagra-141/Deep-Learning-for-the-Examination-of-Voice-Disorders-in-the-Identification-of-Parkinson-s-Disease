"""Run a prediction across all loaded models and assemble the response.

SHAP is computed for a single primary model (the strongest tree-explainable
classifier — LightGBM by default) and surfaced on both the ensemble and the
primary's per-model entry. SHAP failures are non-fatal: the response just
omits the contribution list.
"""
from __future__ import annotations

import datetime
import uuid
import warnings

import numpy as np
import pandas as pd

from app.ml.manager import ModelManager
from app.schemas.feature import VoiceFeatures
from app.schemas.prediction import ModelPredictionOut, PredictionResponse, ShapContribution
from app.services.explainability import compute_shap_top_k

FEATURE_COLUMNS = VoiceFeatures.FEATURE_ORDER

# Models that were fitted WITH a pandas DataFrame (have feature names)
LIGHTGBM_MODELS = {"lightgbm"}

#: Tree-explainable model preferred for SHAP highlighting on the ensemble.
#: Falls back through the list if the preferred isn't loaded.
_PRIMARY_FOR_SHAP: tuple[str, ...] = ("lightgbm", "random_forest", "xgboost", "adaboost")


def _pick_primary(loaded: dict[str, dict]) -> str | None:
    for name in _PRIMARY_FOR_SHAP:
        if name in loaded:
            return name
    return None


def run_prediction(
    features: VoiceFeatures,
    manager: ModelManager,
    input_mode: str,
    *,
    prediction_id: str | None = None,
    created_at: str | None = None,
) -> PredictionResponse:
    """Run prediction on the given features using the loaded models.

    `prediction_id` and `created_at` are accepted as overrides so that callers
    that persist a row first can echo the DB-assigned id and timestamp back to
    the client. When omitted, fresh values are minted.
    """

    # 1. Build raw numpy array (for sklearn models fitted without feature names)
    x_array = np.array([features.to_array()])

    # Scale — scaler was also fitted on a numpy array
    if manager.scaler is None:
        raise RuntimeError("Scaler not loaded.")
    x_scaled_np: np.ndarray = manager.scaler.transform(x_array)

    # Named DataFrame only for LightGBM which expects feature names
    x_scaled_df = pd.DataFrame(x_scaled_np, columns=FEATURE_COLUMNS)

    models = manager.get_all_models()
    if not models:
        raise RuntimeError("No models loaded in the registry.")

    per_model_preds: list[ModelPredictionOut] = []

    for name, m_dict in models.items():
        if name in ("ensemble", "pca_rf"):
            # pca_rf requires a separate PCA transform step not stored in manager
            continue

        model = m_dict["model"]
        version = m_dict["version"]
        calibrator = m_dict["calibrator"]

        # Choose input format based on how the model was trained
        x_input = x_scaled_df if name in LIGHTGBM_MODELS else x_scaled_np

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                label = int(model.predict(x_input)[0])

                if calibrator:
                    prob = float(calibrator.predict(x_input)[0])
                elif hasattr(model, "predict_proba"):
                    prob = float(model.predict_proba(x_input)[0][1])
                elif hasattr(model, "decision_function"):
                    dec = float(model.decision_function(x_input)[0])
                    prob = 1.0 / (1.0 + np.exp(-dec))
                else:
                    prob = float(label)

            per_model_preds.append(
                ModelPredictionOut(
                    model_name=name,
                    model_version=version,
                    label=label,
                    probability=round(prob, 4),
                    shap_top=None,
                )
            )
        except Exception as e:
            print(f"[prediction_service] Model '{name}' failed: {e}")
            continue

    if not per_model_preds:
        raise RuntimeError("No predictions could be generated from any model.")

    # 2. SHAP on the primary model (best-effort; never blocks the response)
    primary_name = _pick_primary(models)
    shap_rows: list[dict] | None = None
    if primary_name is not None:
        primary_bundle = models[primary_name]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            shap_rows = compute_shap_top_k(
                primary_bundle["model"],
                primary_name,
                scaled_features=x_scaled_np[0].tolist(),
                original_values=features.to_array(),
                feature_names=FEATURE_COLUMNS,
                k=5,
            )

    shap_contribs: list[ShapContribution] | None = None
    if shap_rows is not None:
        shap_contribs = [ShapContribution(**r) for r in shap_rows]
        for entry in per_model_preds:
            if entry.model_name == primary_name:
                entry.shap_top = shap_contribs
                break

    # 3. Soft-voting ensemble (average probability)
    avg_prob = sum(p.probability for p in per_model_preds) / len(per_model_preds)
    ensemble_label = 1 if avg_prob > 0.5 else 0

    ensemble_pred = ModelPredictionOut(
        model_name="ensemble",
        model_version="1.0.0",
        label=ensemble_label,
        probability=round(avg_prob, 4),
        shap_top=shap_contribs,
    )

    return PredictionResponse(
        prediction_id=prediction_id or str(uuid.uuid4()),
        created_at=created_at or datetime.datetime.now(datetime.timezone.utc).isoformat(),
        input_mode=input_mode,
        per_model=per_model_preds,
        ensemble=ensemble_pred,
        primary_model=primary_name or "ensemble",
    )
