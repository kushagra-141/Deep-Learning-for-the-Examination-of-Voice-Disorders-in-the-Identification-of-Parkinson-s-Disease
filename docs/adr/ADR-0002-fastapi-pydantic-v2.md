# ADR-0002: FastAPI + Pydantic v2 over Flask/Django

- **Status:** Accepted
- **Date:** 2026-05-01
- **Deciders:** @kushagra

## Context

We need a Python web framework for the REST API. The primary requirement is automatic OpenAPI schema generation (needed to drive TypeScript client codegen). The API must be async-capable to support concurrent audio processing and streaming LLM responses.

## Decision

We will use **FastAPI** with **Pydantic v2** for request/response validation, and **Uvicorn** as the ASGI server.

## Consequences

- **Good:** Auto-generated `/openapi.json` enables `openapi-typescript-codegen` to produce typed API clients — eliminating a whole class of frontend/backend contract bugs.
- **Good:** Pydantic v2 is ~5–10× faster than v1 for validation.
- **Good:** Native async support via `asyncio` — critical for non-blocking audio processing and streaming SSE.
- **Bad:** FastAPI has less out-of-the-box admin/ORM tooling than Django.
- **Risks:** Pydantic v2 has some breaking changes from v1; dependencies that pin v1 may conflict.

## Alternatives Considered

| Alternative | Reason rejected |
|---|---|
| Flask | No async support; no auto OpenAPI; requires extra extensions |
| Django + DRF | Sync by default; heavier; admin is unnecessary for this project |
| Starlette (bare) | FastAPI is a thin wrapper that adds exactly what we need |

## References

- `00_MASTER_PLAN.md §0.6`
- `01_HLD.md §1.3`
