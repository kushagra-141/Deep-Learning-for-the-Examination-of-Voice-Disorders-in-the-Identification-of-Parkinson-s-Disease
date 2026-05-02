"""SHAP contributors tool — reads from the in-memory chat context."""
from __future__ import annotations

from typing import Any

from app.llm.tools import ChatContext, Tool, ToolValidationError


async def _top_shap_handler(*, ctx: ChatContext, k: int = 5) -> dict[str, Any]:
    if not isinstance(k, int) or k <= 0:
        raise ToolValidationError("k must be a positive integer")
    payload = ctx.prediction_payload or {}
    ensemble = payload.get("ensemble") or {}
    shap_top = ensemble.get("shap_top") or []
    contribs = [
        {"feature": s["feature"], "value": s["value"], "shap": s["shap"]}
        for s in shap_top[: min(k, len(shap_top))]
    ]
    return {"primary_model": payload.get("primary_model"), "contributors": contribs}


def top_shap_contributors_tool() -> Tool:
    return Tool(
        name="get_top_shap_contributors",
        description=(
            "Return the top-K SHAP contributors for the user's prediction "
            "(reads from the supplied context — does not recompute)."
        ),
        parameters={
            "type": "object",
            "properties": {
                "k": {
                    "type": "integer",
                    "description": "Number of contributors to return (1–22).",
                    "minimum": 1,
                    "maximum": 22,
                    "default": 5,
                },
            },
            "additionalProperties": False,
        },
        handler=_top_shap_handler,
        features=frozenset({"explainer"}),
        requires_prediction=True,
    )
