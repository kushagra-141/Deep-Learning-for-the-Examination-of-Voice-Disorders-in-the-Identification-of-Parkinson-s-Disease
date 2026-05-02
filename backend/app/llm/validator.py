"""P3.5-05: Output validator.

Runs after the LLM finishes a turn (after the stream is fully assembled but
before persistence / cache write). Two kinds of intervention:

1. **Denylist hits** → replace the assistant's final message with the canned
   refusal from ``refusal_template.md`` and emit a ``policy_violation`` log
   event.
2. **Narrator missing the disclaimer sentence** → append it before
   persistence so the rendered PDF always has it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import structlog

log = structlog.get_logger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"
REFUSAL_TEXT_PATH = PROMPTS_DIR / "refusal_template.md"

NARRATOR_DISCLAIMER = (
    "This summary is for research and educational purposes only and is not a medical diagnosis."
)

# Patterns that indicate the model produced something it shouldn't have.
# Tuned to be conservative: legitimate uses ("the disclaimer says…") still pass
# because we only flag direct second-person diagnostic / treatment language.
_DENYLIST = [
    re.compile(r"\byou\s+(have|likely\s+have|definitely\s+have|are\s+suffering)\b.*\bparkinson", re.IGNORECASE),
    re.compile(r"\bI\s+diagnose\b", re.IGNORECASE),
    re.compile(r"\bI\s+(prescribe|recommend\s+treating)\b", re.IGNORECASE),
    re.compile(r"\bstart\s+taking\b.*\b(levodopa|carbidopa|medication|medicine)\b", re.IGNORECASE),
    re.compile(r"\byou\s+should\s+stop\s+taking\b", re.IGNORECASE),
]

OutcomeT = Literal["ok", "violation", "amended"]


@dataclass(frozen=True)
class ValidationResult:
    outcome: OutcomeT
    text: str
    reason: str | None = None


def _load_refusal() -> str:
    try:
        return REFUSAL_TEXT_PATH.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return (
            "I can't give medical advice. Please consult a qualified neurologist "
            "and see the disclaimer at the bottom of the page."
        )


def check_assistant(text: str) -> ValidationResult:
    """Validate an explainer/help assistant turn.

    Returns the original text if clean, or a refusal message if a denylist
    pattern triggers. Empty input is treated as ``ok`` so partial/cancelled
    streams do not blow up downstream.
    """
    if not text:
        return ValidationResult("ok", text)

    for pattern in _DENYLIST:
        match = pattern.search(text)
        if match:
            log.warning(
                "llm_policy_violation",
                pattern=pattern.pattern,
                snippet=match.group(0)[:80],
            )
            return ValidationResult(
                outcome="violation",
                text=_load_refusal(),
                reason=pattern.pattern,
            )

    return ValidationResult("ok", text)


def check_narrator(text: str) -> ValidationResult:
    """Validate (and amend) a narrator paragraph.

    - Denylist hits are still replaced with the refusal template.
    - If the mandatory disclaimer is missing, append it (case-sensitive match
      since the prompt asks for the exact sentence).
    """
    initial = check_assistant(text)
    if initial.outcome == "violation":
        return initial

    cleaned = (text or "").strip()
    if NARRATOR_DISCLAIMER in cleaned:
        return ValidationResult("ok", cleaned)

    if not cleaned:
        return ValidationResult(
            outcome="amended",
            text=NARRATOR_DISCLAIMER,
            reason="empty_narrator_output",
        )

    sep = "" if cleaned.endswith((".", "!", "?")) else "."
    amended = f"{cleaned}{sep} {NARRATOR_DISCLAIMER}"
    return ValidationResult(outcome="amended", text=amended, reason="missing_disclaimer")
