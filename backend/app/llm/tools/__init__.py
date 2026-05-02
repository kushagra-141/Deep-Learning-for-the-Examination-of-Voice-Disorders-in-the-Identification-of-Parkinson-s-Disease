"""P3.5-04: Tool registry exposed to the LLM.

The LLM may invoke any registered tool whose ``features`` set includes the
current feature (``explainer`` / ``help`` / ``narrator``). Tool handlers are
async and never call out to the network — they read from our own services,
the model registry, or static files.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Literal

import structlog

from app.llm.providers import ToolDef

log = structlog.get_logger(__name__)

FeatureName = Literal["explainer", "help", "narrator"]


class ToolValidationError(Exception):
    """Raised when a tool call's arguments fail validation.

    Recoverable: the orchestrator surfaces this back to the LLM as a tool
    error message so it can react in-conversation rather than crashing.
    """


@dataclass(frozen=True)
class ChatContext:
    """Per-conversation runtime context handed to every tool invocation."""

    session_id: str
    client_fingerprint: str
    prediction_id: str | None
    prediction_features: dict[str, float] | None
    prediction_payload: dict[str, Any] | None
    model_manager: Any | None = None  # injected at orchestrator boundary
    extra: dict[str, Any] = field(default_factory=dict)


Handler = Callable[..., Awaitable[Any]]


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Handler
    features: frozenset[FeatureName]
    requires_prediction: bool = False

    def to_def(self) -> ToolDef:
        return ToolDef(name=self.name, description=self.description, parameters=self.parameters)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool {tool.name!r} already registered")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def for_feature(self, feature: FeatureName) -> list[ToolDef]:
        """Return the tool defs visible to ``feature`` (for the API call)."""
        return [t.to_def() for t in self._tools.values() if feature in t.features]

    async def execute(self, name: str, arguments: dict[str, Any], ctx: ChatContext) -> dict[str, Any]:
        tool = self._tools.get(name)
        if tool is None:
            raise ToolValidationError(f"Unknown tool: {name}")
        if tool.requires_prediction and ctx.prediction_id is None:
            raise ToolValidationError(f"Tool {name!r} requires a prediction context")
        try:
            result = await tool.handler(ctx=ctx, **arguments)
        except ToolValidationError:
            raise
        except Exception as exc:
            log.error("llm_tool_handler_error", tool=name, error=str(exc))
            raise ToolValidationError(f"{name} failed: {exc}") from exc
        if not isinstance(result, dict):
            return {"value": result}
        return result


def build_default_registry() -> ToolRegistry:
    """Construct the canonical registry used by the orchestrator."""
    # Imported lazily so this module stays import-cheap.
    from app.llm.tools.dataset import dataset_summary_tool
    from app.llm.tools.feature import (
        feature_definition_tool,
        feature_population_stats_tool,
    )
    from app.llm.tools.model import model_metric_tool
    from app.llm.tools.shap import top_shap_contributors_tool
    from app.llm.tools.what_if import simulate_what_if_tool

    registry = ToolRegistry()
    registry.register(feature_definition_tool())
    registry.register(feature_population_stats_tool())
    registry.register(top_shap_contributors_tool())
    registry.register(simulate_what_if_tool())
    registry.register(model_metric_tool())
    registry.register(dataset_summary_tool())
    return registry
