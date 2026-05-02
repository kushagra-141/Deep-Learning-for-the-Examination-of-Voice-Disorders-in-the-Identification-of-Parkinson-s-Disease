"""P3.5-09: Help-bot schemas."""
from __future__ import annotations

from pydantic import BaseModel, Field


class HelpRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


class HelpResponse(BaseModel):
    answer: str
    used_corpus: bool = True
