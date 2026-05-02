"""Dataset summary tool."""
from __future__ import annotations

from typing import Any

from app.llm.tools import ChatContext, Tool


async def _dataset_summary_handler(*, ctx: ChatContext) -> dict[str, Any]:
    _ = ctx
    from app.services.analytics import get_dataset_stats

    stats = get_dataset_stats()
    return {
        "total_recordings": stats.total,
        "healthy": stats.by_class.healthy,
        "parkinsons": stats.by_class.parkinsons,
        "feature_count": stats.feature_count,
        "class_balance_pct_parkinsons": stats.class_balance_pct,
        "source": "UCI Parkinson's voice dataset (Little et al., 2007)",
        "license": "Public research dataset",
    }


def dataset_summary_tool() -> Tool:
    return Tool(
        name="get_dataset_summary",
        description=(
            "Return basic facts about the training dataset: total recordings, "
            "class breakdown, feature count, and provenance."
        ),
        parameters={
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
        handler=_dataset_summary_handler,
        features=frozenset({"explainer", "help"}),
    )
