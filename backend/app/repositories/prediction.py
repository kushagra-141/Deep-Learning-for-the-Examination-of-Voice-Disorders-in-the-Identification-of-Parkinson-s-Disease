"""P1-13: Prediction repository."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.prediction import ModelPrediction, Prediction


async def create_prediction(
    db: AsyncSession,
    features: dict[str, Any],
    input_mode: str,
    predictions: list[dict[str, Any]],
    client_fingerprint: str | None = None,
    batch_job_id: uuid.UUID | None = None,
) -> Prediction:
    """Create a new Prediction record with associated ModelPredictions."""
    db_pred = Prediction(
        features=features,
        input_mode=input_mode,
        client_fingerprint=client_fingerprint,
        batch_job_id=batch_job_id,
    )
    db.add(db_pred)
    await db.flush()

    for p in predictions:
        mp = ModelPrediction(
            prediction_id=db_pred.id,
            model_name=p["model_name"],
            model_version=p["model_version"],
            probability=p["probability"],
            label=p["label"],
            shap_values=p.get("shap_values"),
        )
        db.add(mp)
        
    await db.commit()
    await db.refresh(db_pred)
    return db_pred
