"""P3.5-10: Narrate request/response schemas."""
from __future__ import annotations

from pydantic import BaseModel


class NarrateResponse(BaseModel):
    prediction_id: str
    narrative: str
    model: str | None = None
    generated_at: str | None = None
    cached: bool = False
