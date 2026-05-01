# ADR-0014: Grounded-only LLM architecture (no general chat)

- **Status:** Accepted
- **Date:** 2026-05-01
- **Deciders:** @kushagra

## Context

An LLM in a medical-adjacent app can hallucinate diagnostic claims. We need to constrain the LLM to only narrate data that the system already computed.

## Decision

The LLM appears in exactly three grounded contexts:
1. **Chat sidebar** — grounded on a specific `prediction_id`'s data
2. **Help bot** — grounded on a fixed `help_corpus.md` document
3. **Narrator** — one-shot summary of a specific prediction for PDF export

The LLM never receives raw user medical information. It only narrates results that the ML pipeline already produced. All tool calls return structured data, not free text.

## Consequences

- **Good:** Dramatically reduces hallucination risk. The LLM cannot invent a probability — it can only explain one the system computed.
- **Good:** Simplifies the output validator — we know what ground truth data the model should reference.
- **Bad:** The LLM cannot answer general Parkinson's questions outside the app's data.

## References

- `00_MASTER_PLAN.md §0.10, Risk Register R-09`
- `06_LLM_INTEGRATION_LLD.md §6.1`
