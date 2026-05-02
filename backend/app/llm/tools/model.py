"""Tool for reading model metrics from the registry manifest."""
from __future__ import annotations

from typing import Any

from app.llm.tools import ChatContext, Tool, ToolValidationError

ALLOWED_METRICS = {"accuracy", "precision", "recall", "f1", "roc_auc", "cv_accuracy_mean", "cv_accuracy_std"}


async def _model_metric_handler(*, ctx: ChatContext, model_name: str, metric: str) -> dict[str, Any]:
    if metric not in ALLOWED_METRICS:
        raise ToolValidationError(
            f"Unknown metric {metric!r}. Allowed: {', '.join(sorted(ALLOWED_METRICS))}",
        )
    if ctx.model_manager is None:
        raise ToolValidationError("Model manager not available in this context")

    manifest = getattr(ctx.model_manager, "manifest", None)
    if not manifest:
        raise ToolValidationError("Model manifest not loaded")

    entries = {entry["name"]: entry for entry in manifest.get("models", [])}
    entry = entries.get(model_name)
    if entry is None:
        raise ToolValidationError(
            f"Unknown model {model_name!r}. Available: {', '.join(sorted(entries))}",
        )

    metrics = entry.get("metrics") or {}
    if metric not in metrics:
        raise ToolValidationError(
            f"Metric {metric!r} not recorded for {model_name!r}",
        )
    return {"model": model_name, "metric": metric, "value": float(metrics[metric])}


def model_metric_tool() -> Tool:
    return Tool(
        name="get_model_metric",
        description=(
            "Return one performance metric (accuracy, precision, recall, f1, "
            "roc_auc, cv_accuracy_mean, cv_accuracy_std) for a named model "
            "from the trained-model manifest."
        ),
        parameters={
            "type": "object",
            "properties": {
                "model_name": {
                    "type": "string",
                    "description": "Model name as it appears in the registry, e.g. 'lightgbm'.",
                },
                "metric": {
                    "type": "string",
                    "enum": sorted(ALLOWED_METRICS),
                },
            },
            "required": ["model_name", "metric"],
            "additionalProperties": False,
        },
        handler=_model_metric_handler,
        features=frozenset({"explainer"}),
    )
