# ADR-0015: SSE for chat streaming (not WebSocket)

- **Status:** Accepted
- **Date:** 2026-05-01
- **Deciders:** @kushagra

## Context

The LLM chat endpoint needs to stream token deltas to the browser as they are generated. Options are: WebSocket, Server-Sent Events (SSE), or long-polling.

## Decision

Use **SSE** via `sse-starlette` for the `POST /api/v1/chat` endpoint. The frontend uses the `EventSource` API (or a `ReadableStream` fetch for POST requests).

## Consequences

- **Good:** Native browser support; no extra protocol negotiation.
- **Good:** OpenAPI can at least document the endpoint (even if the SSE envelope is not fully typed).
- **Good:** HTTP/1.1 compatible; works through standard reverse proxies (Caddy handles it correctly).
- **Bad:** SSE is unidirectional (server → client). The client must send a new POST for each user message. This is acceptable because each turn is a complete request.
- **Risks:** Some proxies buffer SSE; Caddy with `flush_interval -1` resolves this.

## Alternatives Considered

| Alternative | Reason rejected |
|---|---|
| WebSocket | Requires bi-directional; more complex infra; no native OpenAPI support |
| Long-polling | Higher latency; more requests; worse UX |

## References

- `00_MASTER_PLAN.md §0.6`
- `06_LLM_INTEGRATION_LLD.md §6.5`
