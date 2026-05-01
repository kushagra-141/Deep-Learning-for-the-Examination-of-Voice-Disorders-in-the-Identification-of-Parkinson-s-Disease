"""P1-11: Analytics endpoints (dataset-stats, feature, correlation, pca)."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.analytics import (
    CorrelationMatrix,
    DatasetStats,
    FeatureDistribution,
    PCAProjection,
)
from app.schemas.feature import VoiceFeatures
from app.services import analytics as analytics_service

router = APIRouter()


@router.get("/dataset-stats", response_model=DatasetStats)
async def dataset_stats() -> DatasetStats:
    """Total rows, per-class counts, and class balance (% Parkinson's)."""
    return analytics_service.get_dataset_stats()


@router.get("/feature/{name:path}", response_model=FeatureDistribution)
async def feature_distribution(
    name: str,
    bins: int = Query(30, ge=5, le=100),
) -> FeatureDistribution:
    """Histogram + per-class boxplot stats for one feature.

    `name` must be one of the canonical UCI column names (e.g. `MDVP:Fo(Hz)`).
    """
    try:
        return analytics_service.get_feature_distribution(name, bins=bins)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Unknown feature '{name}'. Allowed values: "
                f"{', '.join(VoiceFeatures.FEATURE_ORDER)}"
            ),
        ) from None


@router.get("/correlation", response_model=CorrelationMatrix)
async def correlation() -> CorrelationMatrix:
    """22x22 Pearson correlation matrix on the bundled dataset."""
    return analytics_service.get_correlation_matrix()


@router.get("/pca", response_model=PCAProjection)
async def pca_projection(
    components: int = Query(2, ge=2, le=3),
) -> PCAProjection:
    """PCA scatter of the dataset, points labeled by class."""
    try:
        return analytics_service.get_pca_projection(components)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
