"""P1-09 + P1-13: Feedback endpoint with DB persistence + rate limit."""
from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter, HTTPException, Request

from app.core.deps import SessionDep
from app.core.rate_limit import limiter
from app.db.models.prediction import Prediction
from app.repositories.feedback import create_feedback
from app.schemas.feedback import FeedbackIn, FeedbackOut

router = APIRouter()
log = structlog.get_logger(__name__)


@router.post("/", response_model=FeedbackOut)
@limiter.limit("5/minute")
async def submit_feedback(
    request: Request,  # noqa: ARG001 — required by slowapi for IP extraction
    body: FeedbackIn,
    db: SessionDep,
) -> FeedbackOut:
    """Persist user feedback against a known prediction.

    The `prediction_id` must reference an existing row — unknown ids return 404
    instead of being silently accepted.
    """
    try:
        pred_uuid = uuid.UUID(body.prediction_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Unknown prediction_id") from None

    pred = await db.get(Prediction, pred_uuid)
    if pred is None:
        raise HTTPException(status_code=404, detail="Unknown prediction_id")

    fb = await create_feedback(db, pred_uuid, body.rating, body.comment)
    log.info(
        "feedback_received",
        feedback_id=str(fb.id),
        prediction_id=body.prediction_id,
        rating=body.rating,
        has_comment=body.comment is not None,
    )
    return FeedbackOut(received=True, feedback_id=str(fb.id))
