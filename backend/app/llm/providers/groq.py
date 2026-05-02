"""Groq provider — primary by default."""
from __future__ import annotations

from app.llm.providers._openai_compat import OpenAICompatProvider

GROQ_BASE_URL = "https://api.groq.com/openai/v1"


class GroqProvider(OpenAICompatProvider):
    def __init__(self, api_key: str, timeout_s: float = 15.0) -> None:
        super().__init__(
            name="groq",
            api_key=api_key,
            base_url=GROQ_BASE_URL,
            timeout_s=timeout_s,
            # Honour Groq's "do not retain prompts for training" header. See
            # docs/06_LLM_INTEGRATION_LLD.md §6.9.
            extra_headers={"x-groq-retention": "off"},
        )
