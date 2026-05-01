"""P1-11: Analytics service — dataset statistics derived from bundled CSV.

All results are deterministic on the bundled dataset, so each function is
memoised with functools.lru_cache to avoid recomputing on every request.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from app.core.config import get_settings
from app.schemas.analytics import (
    BoxplotStats,
    ClassCounts,
    CorrelationMatrix,
    DatasetStats,
    FeatureDistribution,
    PCAPoint,
    PCAProjection,
)
from app.schemas.feature import VoiceFeatures
from app.services.preprocessing import load_dataset


def _dataset_path() -> Path:
    return get_settings().DATA_DIR / "parkinsons.data"


@lru_cache(maxsize=1)
def _df() -> pd.DataFrame:
    return load_dataset(_dataset_path())


@lru_cache(maxsize=1)
def get_dataset_stats() -> DatasetStats:
    df = _df()
    by_class = df["status"].value_counts().to_dict()
    healthy = int(by_class.get(0, 0))
    parkinsons = int(by_class.get(1, 0))
    total = healthy + parkinsons
    return DatasetStats(
        total=total,
        by_class=ClassCounts(healthy=healthy, parkinsons=parkinsons),
        feature_count=len(VoiceFeatures.FEATURE_ORDER),
        class_balance_pct=round(parkinsons / total * 100, 2) if total else 0.0,
    )


def _boxplot_stats(s: pd.Series) -> BoxplotStats:
    return BoxplotStats(
        min=float(s.min()),
        q1=float(s.quantile(0.25)),
        median=float(s.median()),
        q3=float(s.quantile(0.75)),
        max=float(s.max()),
        mean=float(s.mean()),
        std=float(s.std()),
    )


@lru_cache(maxsize=32)
def get_feature_distribution(feature: str, *, bins: int = 30) -> FeatureDistribution:
    if feature not in VoiceFeatures.FEATURE_ORDER:
        raise KeyError(feature)
    df = _df()
    col = df[feature]
    counts, edges = np.histogram(col.values, bins=bins)
    return FeatureDistribution(
        feature=feature,
        bins=[float(b) for b in edges.tolist()],
        counts=[int(c) for c in counts.tolist()],
        by_class={
            "healthy": _boxplot_stats(df.loc[df["status"] == 0, feature]),
            "parkinsons": _boxplot_stats(df.loc[df["status"] == 1, feature]),
        },
    )


@lru_cache(maxsize=1)
def get_correlation_matrix() -> CorrelationMatrix:
    df = _df()
    sub = df[VoiceFeatures.FEATURE_ORDER]
    corr = sub.corr().values
    return CorrelationMatrix(
        features=list(VoiceFeatures.FEATURE_ORDER),
        matrix=[[round(float(v), 4) for v in row] for row in corr],
    )


@lru_cache(maxsize=4)
def get_pca_projection(n_components: int = 2) -> PCAProjection:
    if n_components not in (2, 3):
        raise ValueError("n_components must be 2 or 3")
    df = _df()
    X = df[VoiceFeatures.FEATURE_ORDER].values.astype(float)
    y = df["status"].values.astype(int)
    Xs = StandardScaler().fit_transform(X)
    pca = PCA(n_components=n_components, random_state=1).fit(Xs)
    Xp = pca.transform(Xs)
    points: list[PCAPoint] = []
    for row, label in zip(Xp, y, strict=True):
        # PCAPoint stores 2D coords; for 3D we project to (PC1, PC2) for the
        # default scatter and expose explained_variance for the third axis on
        # the client side. Phase 3 explorer can add a 3D variant later.
        points.append(PCAPoint(x=float(row[0]), y=float(row[1]), label=int(label)))
    return PCAProjection(
        components=n_components,
        explained_variance=[round(float(v), 4) for v in pca.explained_variance_ratio_.tolist()],
        points=points,
    )
