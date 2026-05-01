# ADR-0001: Monorepo with backend/, frontend/, infra/

- **Status:** Accepted
- **Date:** 2026-05-01
- **Deciders:** @kushagra

## Context

We need to decide how to organize the codebase. Options are: monorepo (single repo, multiple packages), polyrepo (separate repos per service), or a hybrid.

The project has a FastAPI backend and a React frontend that share an API contract generated from OpenAPI. A deployment change (e.g., adding a new endpoint) often requires coordinated changes in both the backend and the frontend.

## Decision

We will use a monorepo layout with three top-level directories:
- `backend/` — FastAPI application, ML pipeline, scripts
- `frontend/` — React SPA
- `infra/` — Docker Compose, Caddy, Prometheus, Terraform

A single `Makefile` at the root orchestrates both.

## Consequences

- **Good:** A single PR can change the API contract and the frontend type together. CI is simpler — one workflow file tests both.
- **Good:** OpenAPI codegen can be run in CI and the generated client committed or verified for drift.
- **Bad:** The repo will grow larger over time. Git history mixes backend and frontend commits.
- **Risks:** None significant for a project of this scale (single team, single deployment target).

## Alternatives Considered

| Alternative | Reason rejected |
|---|---|
| Polyrepo | Coordinating API contract drift across repos is error-prone without a schema registry |
| Nx / Turborepo monorepo | Too much tooling overhead for a two-package project |

## References

- `00_MASTER_PLAN.md §0.12`
