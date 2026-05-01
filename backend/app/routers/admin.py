"""P1-08 + P1-13 + P4-02 (partial): Admin-only endpoints with cursor pagination.

Cursor encoding is the ISO8601 `created_at` of the last item on the previous
page. Items are sorted descending by `created_at` so the cursor is the
"before this timestamp" marker.
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.deps import AdminDep, SessionDep
from app.db.models.audit_log import AuditLog
from app.db.models.feedback import Feedback
from app.db.models.prediction import Prediction

router = APIRouter()


def _parse_cursor(cursor: str | None) -> dt.datetime | None:
    if cursor is None:
        return None
    try:
        return dt.datetime.fromisoformat(cursor)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid cursor") from None


@router.get("/me")
async def me(admin: AdminDep) -> dict[str, Any]:
    return {"username": admin.username, "role": admin.role}


@router.get("/predictions")
async def list_predictions(
    admin: AdminDep,  # noqa: ARG001 — gates the route
    db: SessionDep,
    cursor: str | None = None,
    limit: int = Query(50, ge=1, le=200),
) -> dict[str, Any]:
    cursor_dt = _parse_cursor(cursor)
    stmt = (
        select(Prediction)
        .options(selectinload(Prediction.model_predictions))
        .order_by(Prediction.created_at.desc())
        .limit(limit + 1)
    )
    if cursor_dt is not None:
        stmt = stmt.where(Prediction.created_at < cursor_dt)

    rows = list((await db.execute(stmt)).scalars().all())
    has_more = len(rows) > limit
    rows = rows[:limit]
    items = [
        {
            "id": str(r.id),
            "created_at": r.created_at.isoformat(),
            "input_mode": r.input_mode,
            "model_count": len(r.model_predictions),
        }
        for r in rows
    ]
    next_cursor = rows[-1].created_at.isoformat() if has_more and rows else None
    return {"items": items, "next_cursor": next_cursor, "limit": limit, "cursor": cursor}


@router.get("/feedback")
async def list_feedback(
    admin: AdminDep,  # noqa: ARG001
    db: SessionDep,
    cursor: str | None = None,
    limit: int = Query(50, ge=1, le=200),
) -> dict[str, Any]:
    cursor_dt = _parse_cursor(cursor)
    stmt = select(Feedback).order_by(Feedback.created_at.desc()).limit(limit + 1)
    if cursor_dt is not None:
        stmt = stmt.where(Feedback.created_at < cursor_dt)

    rows = list((await db.execute(stmt)).scalars().all())
    has_more = len(rows) > limit
    rows = rows[:limit]
    items = [
        {
            "id": str(r.id),
            "created_at": r.created_at.isoformat(),
            "prediction_id": str(r.prediction_id),
            "rating": r.rating,
            "comment": r.comment,
        }
        for r in rows
    ]
    next_cursor = rows[-1].created_at.isoformat() if has_more and rows else None
    return {"items": items, "next_cursor": next_cursor, "limit": limit, "cursor": cursor}


@router.get("/audit-log")
async def list_audit_log(
    admin: AdminDep,  # noqa: ARG001
    db: SessionDep,
    cursor: str | None = None,
    limit: int = Query(100, ge=1, le=500),
) -> dict[str, Any]:
    cursor_dt = _parse_cursor(cursor)
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit + 1)
    if cursor_dt is not None:
        stmt = stmt.where(AuditLog.created_at < cursor_dt)

    rows = list((await db.execute(stmt)).scalars().all())
    has_more = len(rows) > limit
    rows = rows[:limit]
    items = [
        {
            "id": str(r.id),
            "created_at": r.created_at.isoformat(),
            "actor": r.actor,
            "action": r.action,
            "resource": r.resource,
            "detail": r.detail,
        }
        for r in rows
    ]
    next_cursor = rows[-1].created_at.isoformat() if has_more and rows else None
    return {"items": items, "next_cursor": next_cursor, "limit": limit, "cursor": cursor}
