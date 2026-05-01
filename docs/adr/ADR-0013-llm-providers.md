# ADR-0013: Groq as primary LLM provider, Gemini as fallback

- **Status:** Accepted
- **Date:** 2026-05-01
- **Deciders:** @kushagra

## Context

The LLM layer needs a free-tier provider with sufficient token quota for a demo app. The primary concern is speed (streaming latency) and quota independence between providers.

## Decision

- **Primary:** Groq (`llama-3.3-70b-versatile`) — fastest free tier (~300 tok/s); OpenAI-compatible API
- **Fallback:** Google Gemini (`gemini-2.5-flash`) — independent free quota (~1M tok/day)
- **Optional 3rd:** OpenRouter for additional fallback capacity

All providers are accessed via the `openai` Python SDK with `base_url` swapped.

## Consequences

- **Good:** Two independent providers with independent quotas — high availability.
- **Good:** OpenAI SDK compatibility means one abstraction layer for all three.
- **Bad:** Free tiers can be revoked; rate limits may change. See risk R-10.

## References

- `00_MASTER_PLAN.md §0.6, Risk Register R-10`
- `06_LLM_INTEGRATION_LLD.md §6.2`
