"""P3.5-08: Chat request/response schemas."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """POST body for ``/api/v1/chat``."""

    session_id: str | None = Field(
        default=None,
        description="Persistent session id; server creates one if missing.",
    )
    prediction_id: str | None = Field(
        default=None,
        description="Required for `feature=explainer`. The DB id returned from /predict.",
    )
    message: str = Field(min_length=1, max_length=2000)
    feature: Literal["explainer", "help"] = "explainer"


class ChatChunkOut(BaseModel):
    """One SSE event payload."""

    type: Literal["delta", "tool", "done", "error"]
    delta_text: str | None = None
    tool_name: str | None = None
    tool_status: Literal["called", "ok", "error"] | None = None
    tool_detail: str | None = None
    cached: bool | None = None
    error: str | None = None
    session_id: str | None = None
    request_id: str | None = None
