"""P1-05: Preprocessing — load dataset, split, scale.

Key fix vs original notebook: scaler is fit ONLY on training data,
then applied to the test set using transform() (not fit_transform()).
This eliminates the data-leakage bug in the original notebook.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from app.schemas.feature import VoiceFeatures


def load_dataset(csv_path: Path | str) -> pd.DataFrame:
    """Load parkinsons.data CSV with 'name' as index."""
    df = pd.read_csv(csv_path, sep=",", index_col="name")
    return df


def split_xy(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Extract feature matrix X and label vector y in canonical order."""
    y = df["status"].values.astype(int)
    X = df[VoiceFeatures.FEATURE_ORDER].values.astype(float)
    return X, y


def train_test_split_xy(
    X: np.ndarray,
    y: np.ndarray,
    *,
    test_size: float = 0.2,
    seed: int = 1,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Stratified 80/20 train/test split (reproducible with seed=1)."""
    return train_test_split(X, y, test_size=test_size, random_state=seed, stratify=y)


def fit_scaler(X_train: np.ndarray) -> StandardScaler:
    """Fit StandardScaler on training data only (no leakage)."""
    sc = StandardScaler()
    sc.fit(X_train)
    return sc


def get_train_test(
    csv_path: Path | str,
    *,
    test_size: float = 0.2,
    seed: int = 1,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, StandardScaler]:
    """One-shot helper: load → split → scale.

    Returns (X_train_scaled, X_test_scaled, y_train, y_test, scaler).
    """
    df = load_dataset(csv_path)
    X, y = split_xy(df)
    X_train, X_test, y_train, y_test = train_test_split_xy(X, y, test_size=test_size, seed=seed)
    scaler = fit_scaler(X_train)
    X_train_sc = scaler.transform(X_train)
    X_test_sc = scaler.transform(X_test)
    return X_train_sc, X_test_sc, y_train, y_test, scaler
