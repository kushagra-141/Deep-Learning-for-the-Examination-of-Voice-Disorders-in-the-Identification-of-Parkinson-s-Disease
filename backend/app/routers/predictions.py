"""P3.5-10: prediction-bound endpoints (currently: ``/narrate``).

Mounted under ``/api/v1/predictions``. Distinct from ``/predict`` which only
covers the synchronous prediction call.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

from app.core.config import get_settings
from app.core.deps import AdminDep, SessionDep
from app.core.rate_limit import limiter
from app.llm.budget import BudgetExceeded
from app.llm.providers import LLMUnavailable
from app.schemas.narrate import NarrateResponse
from app.services.narrator import clear_narrative, get_or_create_narrative

router = APIRouter()
_settings = get_settings()


@router.post(
    "/{prediction_id}/narrate",
    response_model=NarrateResponse,
    summary="Generate or fetch a one-paragraph narrative for a prediction",
)
@limiter.limit(f"{_settings.RL_PREDICT_PER_MIN}/minute")
async def narrate(
    request: Request,
    prediction_id: str,
    db: SessionDep,
) -> NarrateResponse:
    client_fp = request.client.host if request.client else "anonymous"
    try:
        return await get_or_create_narrative(
            db,
            prediction_id,
            client_fingerprint=client_fp,
        )
    except LookupError:
        raise HTTPException(status_code=404, detail="prediction not found") from None
    except BudgetExceeded as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"daily token budget exceeded ({exc.scope})",
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from None
    except LLMUnavailable:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The narrator is unavailable right now.",
        ) from None


@router.delete(
    "/{prediction_id}/narrate",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Force regeneration by clearing the cached narrative (admin only)",
)
async def clear(prediction_id: str, _admin: AdminDep, db: SessionDep) -> None:
    cleared = await clear_narrative(db, prediction_id)
    if not cleared:
        raise HTTPException(status_code=404, detail="prediction not found")
