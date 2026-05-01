"""Prediction request/response schemas."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.feature import VoiceFeatures

MODEL_NAMES = Literal[
    "knn", "svm", "decision_tree", "bagging", "lightgbm",
    "adaboost", "random_forest", "xgboost", "pca_rf", "ensemble",
]

MEDICAL_DISCLAIMER = (
    "Research and educational demonstration only. "
    "NOT a diagnostic device. "
    "Consult a qualified neurologist for any medical concern."
)


class PredictionRequest(BaseModel):
    features: VoiceFeatures
    model_name: MODEL_NAMES | None = None  # None = run all + ensemble


class ShapContribution(BaseModel):
    feature: str
    value: float  # original feature value
    shap: float   # SHAP contribution (signed)


class ModelPredictionOut(BaseModel):
    model_name: str
    model_version: str
    label: int = Field(ge=0, le=1)
    probability: float = Field(ge=0.0, le=1.0)
    shap_top: list[ShapContribution] | None = None  # top-5 by |shap|


class PredictionResponse(BaseModel):
    prediction_id: str
    created_at: str  # ISO8601 UTC
    input_mode: Literal["manual", "audio", "batch"]
    per_model: list[ModelPredictionOut]
    ensemble: ModelPredictionOut
    primary_model: str  # the model whose SHAP is highlighted
    disclaimer: str = MEDICAL_DISCLAIMER
