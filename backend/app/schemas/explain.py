"""P1-12: Schemas for LLM Explainability."""
from pydantic import BaseModel, Field
from typing import Dict, Any


class ExplainRequest(BaseModel):
    features: Dict[str, float] = Field(
        ...,
        description="The 22 acoustic features used for the prediction.",
    )
    probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="The ensemble probability of Parkinson's disease.",
    )
    input_mode: str = Field(
        default="manual",
        description="Whether the features were manually entered or extracted from audio.",
    )
