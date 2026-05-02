"""P3.5: LLM integration layer.

The LLM layer wraps the three free-tier providers (Groq, Gemini, OpenRouter)
behind a uniform OpenAI-compatible streaming interface, layers a primary/
fallback router with a circuit breaker on top, and exposes three endpoints:

- ``POST /api/v1/chat`` — SSE-streamed result-grounded explainer
- ``POST /api/v1/help`` — non-streaming FAQ bot
- ``POST /api/v1/predictions/{id}/narrate`` — one-shot PDF narrator

See ``docs/06_LLM_INTEGRATION_LLD.md`` for the full design.
"""
