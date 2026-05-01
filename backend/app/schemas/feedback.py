"""Feedback schemas (LLD §2.4.3, §2.7.7)."""
from __future__ import annotations

from pydantic import BaseModel, Field


class FeedbackIn(BaseModel):
    prediction_id: str = Field(min_length=1, max_length=64)
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=2000)


class FeedbackOut(BaseModel):
    received: bool = True
    feedback_id: str
