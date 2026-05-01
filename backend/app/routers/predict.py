"""P1-09 + P1-13: Prediction endpoints (POST /predict, GET /predict/sample).

Persistence: every successful POST writes a `predictions` row plus N
`model_predictions` rows. The DB-assigned id and created_at are echoed back
to the client so the FE can use them as a stable identifier (e.g. for
feedback or share links).
"""
from __future__ import annotations

import random
from functools import lru_cache
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request

from app.core.config import get_settings
from app.core.deps import SessionDep
from app.core.rate_limit import limiter
from app.repositories.prediction import create_prediction
from app.schemas.feature import VoiceFeatures
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.services.prediction_service import run_prediction
from app.services.preprocessing import load_dataset

router = APIRouter()
_settings = get_settings()


async def _persist_and_run(
    features: VoiceFeatures,
    manager: object,
    input_mode: str,
    db: SessionDep,
) -> PredictionResponse:
    """Compute predictions, persist them, and return the response with DB ids."""
    response = run_prediction(features, manager, input_mode)
    rows = [
        {
            "model_name": m.model_name,
            "model_version": m.model_version,
            "probability": m.probability,
            "label": m.label,
            "shap_values": (
                {"top": [c.model_dump() for c in m.shap_top]} if m.shap_top else None
            ),
        }
        for m in [*response.per_model, response.ensemble]
    ]
    pred = await create_prediction(
        db,
        features=features.model_dump(by_alias=True),
        input_mode=input_mode,
        predictions=rows,
    )
    response.prediction_id = str(pred.id)
    response.created_at = pred.created_at.isoformat()
    return response


@router.post("/", response_model=PredictionResponse)
@limiter.limit(f"{_settings.RL_PREDICT_PER_MIN}/minute")
async def predict_features(
    request: Request, body: PredictionRequest, db: SessionDep
) -> PredictionResponse:
    """Predict Parkinson's from a 22-feature payload."""
    manager = request.app.state.model_manager
    return await _persist_and_run(body.features, manager, "manual", db)


@lru_cache(maxsize=1)
def _samples_by_class() -> dict[int, list[VoiceFeatures]]:
    df = load_dataset(get_settings().DATA_DIR / "parkinsons.data")
    out: dict[int, list[VoiceFeatures]] = {0: [], 1: []}
    for _, row in df.iterrows():
        payload = {col: float(row[col]) for col in VoiceFeatures.FEATURE_ORDER}
        out[int(row["status"])].append(VoiceFeatures.model_validate(payload))
    return out


@router.get("/sample", response_model=VoiceFeatures, response_model_by_alias=True)
async def predict_sample(
    label: Literal["0", "1", "random"] = Query(
        "random",
        description="0 = healthy, 1 = Parkinson's, random = pick from either class",
    ),
) -> VoiceFeatures:
    """Return a randomly chosen row from the bundled dataset as a `VoiceFeatures` payload."""
    pool = _samples_by_class()
    if label == "random":
        choices = pool[0] + pool[1]
    else:
        choices = pool[int(label)]
    if not choices:
        raise HTTPException(status_code=503, detail="Dataset empty or unreadable")
    return random.choice(choices)  # noqa: S311 — non-cryptographic sampling
