"""Batch job schemas (LLD §2.4.3, §2.7.4)."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

BatchStatus = Literal["queued", "running", "succeeded", "failed"]


class BatchJobCreated(BaseModel):
    job_id: str
    status_url: str


class BatchJobStatus(BaseModel):
    id: str
    status: BatchStatus
    progress: float = Field(ge=0.0, le=1.0, description="0..1")
    row_count: int = Field(ge=0)
    error: str | None = None
