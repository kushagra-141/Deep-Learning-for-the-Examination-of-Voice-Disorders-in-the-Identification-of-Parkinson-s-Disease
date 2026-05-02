"""P3.5-08: Chat router (SSE).

Streams orchestrator events back to the client as Server-Sent Events. Each
SSE ``data:`` payload is the JSON-encoded form of :class:`ChatChunkOut`.

Heartbeats: ``sse-starlette`` already emits its own ``ping_message`` every
``ping`` seconds; we set 15 s to match the LLD.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from typing import AsyncIterator

import structlog
from fastapi import APIRouter, HTTPException, Request, status
from sse_starlette.sse import EventSourceResponse

from app.core.config import get_settings
from app.core.deps import SessionDep
from app.core.rate_limit import limiter
from app.db.models.prediction import ModelPrediction, Prediction
from app.llm.budget import BudgetExceeded
from app.llm.orchestrator import (
    DeltaEvent,
    DoneEvent,
    ErrorEvent,
    ToolEvent,
    get_orchestrator,
)
from app.llm.session import new_session_id
from app.schemas.chat import ChatChunkOut, ChatRequest
from sqlalchemy import select

router = APIRouter()
log = structlog.get_logger(__name__)
_settings = get_settings()


async def _load_prediction_payload(db: SessionDep, prediction_id: str) -> dict | None:
    """Hydrate a stored prediction into the same shape the frontend received.

    Returns ``None`` if the id is malformed or the row is not found — chat
    router converts that to a 404 before opening the SSE stream.
    """
    try:
        pred_uuid = uuid.UUID(prediction_id)
    except ValueError:
        return None
    stmt = select(Prediction).where(Prediction.id == pred_uuid)
    pred = (await db.execute(stmt)).scalar_one_or_none()
    if pred is None:
        return None
    mp_stmt = select(ModelPrediction).where(ModelPrediction.prediction_id == pred.id)
    rows = list((await db.execute(mp_stmt)).scalars().all())

    per_model: list[dict] = []
    ensemble: dict | None = None
    primary_model: str = "ensemble"
    for r in rows:
        item = {
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
        if r.shap_values and isinstance(r.shap_values, dict) and r.shap_values.get("top"):
            primary_model = r.model_name if r.model_name != "ensemble" else primary_model

    return {
        "prediction_id": str(pred.id),
        "created_at": pred.created_at.isoformat(),
        "input_mode": pred.input_mode,
        "features": pred.features,
        "per_model": per_model,
        "ensemble": ensemble or {},
        "primary_model": primary_model,
    }


def _to_chunk_out(
    event: DeltaEvent | ToolEvent | DoneEvent | ErrorEvent,
    *,
    session_id: str,
    request_id: str,
) -> ChatChunkOut:
    if isinstance(event, DeltaEvent):
        return ChatChunkOut(
            type="delta",
            delta_text=event.text,
            session_id=session_id,
            request_id=request_id,
        )
    if isinstance(event, ToolEvent):
        return ChatChunkOut(
            type="tool",
            tool_name=event.name,
            tool_status=event.status,
            tool_detail=event.detail,
            session_id=session_id,
            request_id=request_id,
        )
    if isinstance(event, DoneEvent):
        return ChatChunkOut(
            type="done",
            cached=event.cached,
            session_id=session_id,
            request_id=request_id,
        )
    return ChatChunkOut(
        type="error",
        error=event.message,
        session_id=session_id,
        request_id=request_id,
    )


@router.post("/", summary="Stream a chat reply (SSE)")
@limiter.limit(f"{_settings.RL_PREDICT_PER_MIN}/minute")
async def chat_stream(
    request: Request,
    body: ChatRequest,
    db: SessionDep,
) -> EventSourceResponse:
    if body.feature == "explainer" and not body.prediction_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="prediction_id is required for the explainer feature",
        )

    prediction_payload: dict | None = None
    if body.feature == "explainer":
        prediction_payload = await _load_prediction_payload(db, body.prediction_id or "")
        if prediction_payload is None:
            raise HTTPException(status_code=404, detail="prediction not found")

    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    client_fp = request.client.host if request.client else "anonymous"
    session_id = body.session_id or new_session_id()
    orchestrator = get_orchestrator()
    ctx = orchestrator.build_context(
        session_id=session_id,
        client_fingerprint=client_fp,
        prediction_payload=prediction_payload,
        model_manager=request.app.state.model_manager,
    )

    async def event_source() -> AsyncIterator[dict]:
        # Always emit a session id up front so the client can resume.
        yield {
            "event": "ready",
            "data": json.dumps({"session_id": session_id, "request_id": request_id}),
        }
        try:
            async for ev in orchestrator.run(
                feature=body.feature,
                user_message=body.message,
                ctx=ctx,
            ):
                if await request.is_disconnected():
                    log.info("chat_stream_client_disconnected", session_id=session_id)
                    return
                payload = _to_chunk_out(ev, session_id=session_id, request_id=request_id)
                yield {
                    "event": payload.type,
                    "data": payload.model_dump_json(exclude_none=True),
                }
                if payload.type in ("done", "error"):
                    return
        except BudgetExceeded as exc:
            payload = ChatChunkOut(
                type="error",
                error=f"daily token budget exceeded ({exc.scope})",
                session_id=session_id,
                request_id=request_id,
            )
            yield {"event": "error", "data": payload.model_dump_json(exclude_none=True)}
        except asyncio.CancelledError:  # pragma: no cover — abort
            raise
        except Exception as exc:  # noqa: BLE001 — surface any unexpected failure
            log.exception("chat_stream_unexpected_failure", error=str(exc))
            payload = ChatChunkOut(
                type="error",
                error="internal error",
                session_id=session_id,
                request_id=request_id,
            )
            yield {"event": "error", "data": payload.model_dump_json(exclude_none=True)}

    return EventSourceResponse(event_source(), ping=15)
