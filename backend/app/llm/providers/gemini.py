"""Google Gemini provider — fallback by default.

Uses Gemini's OpenAI-compatible endpoint so we can share one streaming client.
"""
from __future__ import annotations

from app.llm.providers._openai_compat import OpenAICompatProvider

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"


class GeminiProvider(OpenAICompatProvider):
    def __init__(self, api_key: str, timeout_s: float = 15.0) -> None:
        super().__init__(
            name="gemini",
            api_key=api_key,
            base_url=GEMINI_BASE_URL,
            timeout_s=timeout_s,
        )
