"""P1-07: Voting ensemble logic."""
from __future__ import annotations

import numpy as np


def compute_ensemble_prediction(probabilities: list[float]) -> dict:
    """Soft voting ensemble: averages the predicted probabilities.
    
    Args:
        probabilities: List of positive class probabilities from base models.
    """
    if not probabilities:
        return {"probability": 0.0, "label": 0}
        
    avg_prob = float(np.mean(probabilities))
    label = 1 if avg_prob >= 0.5 else 0
    return {"probability": avg_prob, "label": label}
