"""OpenRouter provider — optional 3rd choice."""
from __future__ import annotations

from app.llm.providers._openai_compat import OpenAICompatProvider

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterProvider(OpenAICompatProvider):
    def __init__(self, api_key: str, timeout_s: float = 15.0) -> None:
        super().__init__(
            name="openrouter",
            api_key=api_key,
            base_url=OPENROUTER_BASE_URL,
            timeout_s=timeout_s,
            extra_headers={"X-Title": "Parkinson's Voice Detection"},
        )
