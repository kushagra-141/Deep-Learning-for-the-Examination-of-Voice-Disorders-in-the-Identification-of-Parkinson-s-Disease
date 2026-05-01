"""Model info schemas."""
from __future__ import annotations

from pydantic import BaseModel


class ConfusionMatrix(BaseModel):
    tn: int
    fp: int
    fn: int
    tp: int


class ModelMetrics(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float
    confusion_matrix: ConfusionMatrix
    cv_accuracy_mean: float
    cv_accuracy_std: float


class ModelInfo(BaseModel):
    name: str
    version: str
    metrics: ModelMetrics
    hyperparameters: dict
    trained_at: str  # ISO8601


class ModelComparison(BaseModel):
    models: list[ModelInfo]
