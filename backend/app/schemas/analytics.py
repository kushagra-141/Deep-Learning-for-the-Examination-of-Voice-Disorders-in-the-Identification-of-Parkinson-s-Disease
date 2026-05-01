"""Analytics response schemas (LLD §2.4.3, §2.7.6)."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ClassCounts(BaseModel):
    healthy: int = Field(ge=0, description="status=0 row count")
    parkinsons: int = Field(ge=0, description="status=1 row count")


class DatasetStats(BaseModel):
    total: int = Field(ge=0)
    by_class: ClassCounts
    feature_count: int = Field(ge=0)
    class_balance_pct: float = Field(ge=0.0, le=100.0, description="% Parkinson's")


class BoxplotStats(BaseModel):
    min: float
    q1: float
    median: float
    q3: float
    max: float
    mean: float
    std: float


class FeatureDistribution(BaseModel):
    feature: str
    bins: list[float] = Field(description="Histogram bin edges (length = counts+1)")
    counts: list[int] = Field(description="Histogram counts per bin")
    by_class: dict[str, BoxplotStats] = Field(
        description="Boxplot stats keyed by 'healthy' / 'parkinsons'"
    )


class CorrelationMatrix(BaseModel):
    features: list[str]
    matrix: list[list[float]]


class PCAPoint(BaseModel):
    x: float
    y: float
    label: int


class PCAProjection(BaseModel):
    components: int = Field(ge=2, le=3, description="Number of components in returned points")
    explained_variance: list[float] = Field(description="Variance ratio per component")
    points: list[PCAPoint]
