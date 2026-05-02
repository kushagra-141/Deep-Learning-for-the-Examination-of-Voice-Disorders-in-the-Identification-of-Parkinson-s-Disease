"""Feature-related tools: definition lookup + population statistics."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.llm.tools import ChatContext, Tool, ToolValidationError
from app.schemas.feature import VoiceFeatures


GLOSSARY_PATH = Path(__file__).resolve().parents[1] / "glossary.json"


@lru_cache(maxsize=1)
def _glossary() -> dict[str, dict[str, str]]:
    if not GLOSSARY_PATH.exists():
        return {}
    return json.loads(GLOSSARY_PATH.read_text(encoding="utf-8"))


def _validate_feature_name(name: str) -> None:
    if name not in VoiceFeatures.FEATURE_ORDER:
        raise ToolValidationError(
            f"Unknown feature {name!r}. Allowed: {', '.join(VoiceFeatures.FEATURE_ORDER)}",
        )


# ── get_feature_definition ──────────────────────────────────────────────────

async def _feature_definition_handler(*, ctx: ChatContext, name: str) -> dict[str, Any]:
    _ = ctx  # unused
    _validate_feature_name(name)
    entry = _glossary().get(name)
    if not entry:
        raise ToolValidationError(f"No glossary entry for {name!r}")
    return {"feature": name, **entry}


def feature_definition_tool() -> Tool:
    return Tool(
        name="get_feature_definition",
        description=(
            "Return the plain-English definition, unit, normal range, and "
            "interpretation of a single acoustic feature."
        ),
        parameters={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Canonical feature name, e.g. 'MDVP:Jitter(%)' or 'PPE'.",
                    "enum": list(VoiceFeatures.FEATURE_ORDER),
                },
            },
            "required": ["name"],
            "additionalProperties": False,
        },
        handler=_feature_definition_handler,
        features=frozenset({"explainer", "help"}),
    )


# ── get_feature_population_stats ────────────────────────────────────────────

async def _feature_population_handler(*, ctx: ChatContext, name: str) -> dict[str, Any]:
    _ = ctx
    _validate_feature_name(name)
    # Late import: keeps the heavy pandas/sklearn stack out of import time
    # for processes that never call this tool.
    from app.services.analytics import get_feature_distribution

    dist = get_feature_distribution(name, bins=30)
    healthy = dist.by_class["healthy"]
    parkinsons = dist.by_class["parkinsons"]
    return {
        "feature": name,
        "min": healthy.min if healthy.min < parkinsons.min else parkinsons.min,
        "max": healthy.max if healthy.max > parkinsons.max else parkinsons.max,
        "p10": healthy.q1,  # approximation — analytics service exposes quartiles, not deciles
        "p50": healthy.median,
        "p90": healthy.q3,
        "mean_healthy": healthy.mean,
        "mean_parkinsons": parkinsons.mean,
        "std_healthy": healthy.std,
        "std_parkinsons": parkinsons.std,
    }


def feature_population_stats_tool() -> Tool:
    return Tool(
        name="get_feature_population_stats",
        description=(
            "Return summary statistics for one feature across the dataset, "
            "broken down by class (healthy vs Parkinson's). Useful when the "
            "user asks 'is my value high?' or 'how does this compare?'."
        ),
        parameters={
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Canonical feature name.",
                    "enum": list(VoiceFeatures.FEATURE_ORDER),
                },
            },
            "required": ["name"],
            "additionalProperties": False,
        },
        handler=_feature_population_handler,
        features=frozenset({"explainer"}),
    )
