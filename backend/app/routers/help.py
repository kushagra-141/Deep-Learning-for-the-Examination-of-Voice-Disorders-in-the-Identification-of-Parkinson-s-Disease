"""P3.5-09: Help endpoint — non-streaming, corpus-grounded.

Calls the orchestrator's one-shot ``help_once`` and returns the full answer.
The off-corpus signal we look for (verbatim string from `help_system.md`) is
preserved by the model when the question isn't covered.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.llm.budget import BudgetExceeded
from app.llm.orchestrator import get_orchestrator
from app.llm.providers import LLMUnavailable
from app.schemas.help import HelpRequest, HelpResponse

router = APIRouter()
_settings = get_settings()

OUT_OF_DOCS_MARKER = "outside my docs"


@router.post("/", response_model=HelpResponse, summary="Ask the FAQ bot a single question")
@limiter.limit(f"{_settings.RL_PREDICT_PER_MIN}/minute")
async def ask_help(request: Request, body: HelpRequest) -> HelpResponse:
    client_fp = request.client.host if request.client else "anonymous"
    orchestrator = get_orchestrator()
    try:
        answer, _usage = await orchestrator.help_once(
            question=body.question,
            client_fingerprint=client_fp,
        )
    except BudgetExceeded as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"daily token budget exceeded ({exc.scope})",
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from None
    except LLMUnavailable:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The help bot is unavailable right now.",
        ) from None

    used_corpus = OUT_OF_DOCS_MARKER not in answer.lower()
    return HelpResponse(answer=answer, used_corpus=used_corpus)
