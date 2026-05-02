"""Build a configured :class:`ProviderRouter` from settings.

Centralising provider construction keeps the choice of primary/fallback in
one place so config changes don't ripple through the orchestrator/routers.
"""
from __future__ import annotations

from functools import lru_cache

import structlog

from app.core.config import Settings, get_settings
from app.llm.providers import (
    GeminiProvider,
    GroqProvider,
    LLMProvider,
    OpenRouterProvider,
)
from app.llm.router import ProviderRouter

log = structlog.get_logger(__name__)


# Per-feature default models. Mirrors §6.2.3 of the LLM LLD.
DEFAULT_TASK_MODELS: dict[str, dict[str, str]] = {
    "groq": {
        "explainer": "llama-3.3-70b-versatile",
        "help": "llama-3.1-8b-instant",
        "narrator": "llama-3.1-8b-instant",
    },
    "gemini": {
        "explainer": "gemini-2.5-flash",
        "help": "gemini-2.5-flash",
        "narrator": "gemini-2.5-flash",
    },
    "openrouter": {
        "explainer": "meta-llama/llama-3.3-70b-instruct:free",
        "help": "meta-llama/llama-3.3-70b-instruct:free",
        "narrator": "meta-llama/llama-3.3-70b-instruct:free",
    },
}


def _build_provider(name: str, settings: Settings) -> LLMProvider | None:
    timeout = float(settings.LLM_TIMEOUT_S)
    if name == "groq" and settings.GROQ_API_KEY is not None:
        return GroqProvider(settings.GROQ_API_KEY.get_secret_value(), timeout_s=timeout)
    if name == "gemini" and settings.GEMINI_API_KEY is not None:
        return GeminiProvider(settings.GEMINI_API_KEY.get_secret_value(), timeout_s=timeout)
    if name == "openrouter" and settings.OPENROUTER_API_KEY is not None:
        return OpenRouterProvider(
            settings.OPENROUTER_API_KEY.get_secret_value(), timeout_s=timeout
        )
    return None


@lru_cache(maxsize=1)
def get_router() -> ProviderRouter:
    """Return the singleton router built from current settings."""
    settings = get_settings()
    primary_name = settings.LLM_PRIMARY_PROVIDER
    fallback_name = settings.LLM_FALLBACK_PROVIDER

    primary = _build_provider(primary_name, settings)
    if primary is None:
        # Pick the first provider with a configured key — keep the app starting
        # even when only the fallback's key is present in dev.
        for candidate in ("groq", "gemini", "openrouter"):
            primary = _build_provider(candidate, settings)
            if primary is not None:
                primary_name = candidate
                break
    if primary is None:
        raise RuntimeError(
            "No LLM provider key is configured. Set GROQ_API_KEY, GEMINI_API_KEY, "
            "or OPENROUTER_API_KEY.",
        )

    fallback = _build_provider(fallback_name, settings) if fallback_name != primary_name else None
    if fallback is None:
        for candidate in ("gemini", "groq", "openrouter"):
            if candidate == primary_name:
                continue
            fallback = _build_provider(candidate, settings)
            if fallback is not None:
                break

    log.info(
        "llm_router_initialised",
        primary=primary.name,
        fallback=fallback.name if fallback else None,
    )
    return ProviderRouter(primary=primary, fallback=fallback)


def model_for(feature: str, provider_name: str) -> str:
    """Resolve the default model for ``(provider, feature)``."""
    table = DEFAULT_TASK_MODELS.get(provider_name) or DEFAULT_TASK_MODELS["groq"]
    return table.get(feature, table["explainer"])
