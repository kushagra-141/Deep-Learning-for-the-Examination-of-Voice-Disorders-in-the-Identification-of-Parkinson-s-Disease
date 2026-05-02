"""What-if simulation tool.

Validates the requested feature overrides against :class:`VoiceFeatures` and
re-runs the prediction service WITHOUT persisting the result. Per LLD §6.8.3
we cap the number of features that can be changed in a single call to 5 to
keep the LLM from sweeping the whole feature space.
"""
from __future__ import annotations

from typing import Any

from app.llm.tools import ChatContext, Tool, ToolValidationError
from app.schemas.feature import VoiceFeatures

MAX_UPDATES_PER_CALL = 5


async def _simulate_handler(*, ctx: ChatContext, updates: dict[str, float]) -> dict[str, Any]:
    if ctx.prediction_features is None:
        raise ToolValidationError(
            "simulate_what_if requires the prediction context. Try the normal /predict flow instead.",
        )
    if not isinstance(updates, dict) or not updates:
        raise ToolValidationError("'updates' must be a non-empty object of feature → number")
    if len(updates) > MAX_UPDATES_PER_CALL:
        raise ToolValidationError(
            f"Cannot change more than {MAX_UPDATES_PER_CALL} features in one call.",
        )

    merged = dict(ctx.prediction_features)
    invalid: list[str] = []
    for name, raw in updates.items():
        if name not in VoiceFeatures.FEATURE_ORDER:
            invalid.append(name)
            continue
        try:
            merged[name] = float(raw)
        except (TypeError, ValueError):
            invalid.append(name)
    if invalid:
        raise ToolValidationError(f"Unknown or non-numeric features: {', '.join(invalid)}")

    # Validate the merged payload against VoiceFeatures (range + completeness).
    try:
        validated = VoiceFeatures.model_validate(merged)
    except Exception as exc:  # pydantic ValidationError
        raise ToolValidationError(f"Resulting feature payload is invalid: {exc}") from exc

    if ctx.model_manager is None:
        raise ToolValidationError("Model manager not available in this context")

    # Late import — heavy ML stack; ensures startup cost stays low for processes
    # that never invoke the tool.
    from app.services.prediction_service import run_prediction

    response = run_prediction(validated, ctx.model_manager, input_mode="manual")
    return {
        "ensemble_probability": response.ensemble.probability,
        "ensemble_label": response.ensemble.label,
        "primary_model": response.primary_model,
        "top_shap": [c.model_dump() for c in (response.ensemble.shap_top or [])],
        "per_model": [
            {"model": p.model_name, "probability": p.probability, "label": p.label}
            for p in response.per_model
        ],
    }


def simulate_what_if_tool() -> Tool:
    return Tool(
        name="simulate_what_if",
        description=(
            "Re-run the model with one or more feature values overridden, "
            "holding all other features fixed. Use this when the user asks "
            "'what if X was Y?'. Does NOT persist the simulated prediction."
        ),
        parameters={
            "type": "object",
            "properties": {
                "updates": {
                    "type": "object",
                    "description": (
                        "Map of feature name to new numeric value; only the 22 canonical "
                        "features are accepted, max 5 features per call."
                    ),
                    "additionalProperties": {"type": "number"},
                },
            },
            "required": ["updates"],
            "additionalProperties": False,
        },
        handler=_simulate_handler,
        features=frozenset({"explainer"}),
        requires_prediction=True,
    )
