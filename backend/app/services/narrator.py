"""P3.5-10: PDF-bound narrator service.

Loads a stored prediction, asks the orchestrator for a one-paragraph
narrative, persists it on the row, and returns the result. Idempotent:
subsequent calls return the cached row without invoking the LLM.
"""
from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.prediction import ModelPrediction, Prediction
from app.llm.orchestrator import get_orchestrator
from app.schemas.narrate import NarrateResponse

log = structlog.get_logger(__name__)


async def _load_prediction(db: AsyncSession, prediction_id: str) -> Prediction | None:
    try:
        pid = uuid.UUID(prediction_id)
    except ValueError:
        return None
    return (
        await db.execute(select(Prediction).where(Prediction.id == pid))
    ).scalar_one_or_none()


def _build_payload(pred: Prediction, rows: list[ModelPrediction]) -> dict[str, Any]:
    per_model: list[dict[str, Any]] = []
    ensemble: dict[str, Any] = {}
    for r in rows:
        item: dict[str, Any] = {
            "model_name": r.model_name,
            "model_version": r.model_version,
            "label": int(r.label),
            "probability": float(r.probability),
            "shap_top": (r.shap_values or {}).get("top") if isinstance(r.shap_values, dict) else None,
        }
        if r.model_name == "ensemble":
            ensemble = item
        else:
            per_model.append(item)
    return {
        "prediction_id": str(pred.id),
        "input_mode": pred.input_mode,
        "features": pred.features,
        "ensemble": ensemble,
        "per_model": per_model,
    }


async def get_or_create_narrative(
    db: AsyncSession,
    prediction_id: str,
    *,
    client_fingerprint: str,
    force: bool = False,
) -> NarrateResponse:
    """Return the cached narrative if present, otherwise generate one.

    On generation failure (provider down, budget exceeded), raises the
    underlying exception so the route can decide whether to 503 or surface a
    static placeholder. Persistence happens within the caller's session.
    """
    pred = await _load_prediction(db, prediction_id)
    if pred is None:
        raise LookupError("prediction not found")

    if not force and pred.narrative:
        return NarrateResponse(
            prediction_id=str(pred.id),
            narrative=pred.narrative,
            model=pred.narrative_model,
            generated_at=pred.narrative_generated_at.isoformat() if pred.narrative_generated_at else None,
            cached=True,
        )

    rows_stmt = select(ModelPrediction).where(ModelPrediction.prediction_id == pred.id)
    rows = list((await db.execute(rows_stmt)).scalars().all())
    payload = _build_payload(pred, rows)

    orchestrator = get_orchestrator()
    text, model_name, _usage = await orchestrator.narrate_once(
        prediction_payload=payload,
        client_fingerprint=client_fingerprint,
    )

    pred.narrative = text
    pred.narrative_model = model_name
    pred.narrative_generated_at = dt.datetime.now(dt.timezone.utc)
    await db.commit()
    await db.refresh(pred)

    return NarrateResponse(
        prediction_id=str(pred.id),
        narrative=text,
        model=model_name,
        generated_at=pred.narrative_generated_at.isoformat() if pred.narrative_generated_at else None,
        cached=False,
    )


async def clear_narrative(db: AsyncSession, prediction_id: str) -> bool:
    """Wipe an existing narrative (admin action). Returns True if a row was touched."""
    pred = await _load_prediction(db, prediction_id)
    if pred is None:
        return False
    pred.narrative = None
    pred.narrative_model = None
    pred.narrative_generated_at = None
    await db.commit()
    return True
