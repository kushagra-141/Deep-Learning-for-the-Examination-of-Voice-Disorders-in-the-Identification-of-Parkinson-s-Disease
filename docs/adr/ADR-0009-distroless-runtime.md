# ADR-0009: Distroless runtime image for API

- **Status:** Accepted
- **Date:** 2026-05-01
- **Deciders:** @kushagra

## Context

The backend Docker image needs to be small, secure, and production-ready. Options range from full Ubuntu/Debian images to minimal base images.

## Decision

We will use a **multi-stage Dockerfile** for the backend:
1. **Build stage**: `python:3.11-slim-bookworm` — installs all dependencies
2. **Runtime stage**: `gcr.io/distroless/python3-debian12` — copies only the installed packages and application code

## Consequences

- **Good:** Distroless images contain no shell, package manager, or other tools that could be exploited in a container escape. Dramatically reduces the attack surface.
- **Good:** Smaller image size (~200 MB vs ~500 MB for full Python).
- **Bad:** No shell in the container for debugging. Mitigation: use `docker exec` with a debug sidecar image during incidents (documented in runbook).
- **Risks:** `parselmouth` requires native compilation — the build stage must use a full `python:3.11` image with build tools. The final stage copies the compiled wheels.

## Alternatives Considered

| Alternative | Reason rejected |
|---|---|
| `python:3.11-slim` | Has a shell and package manager — unnecessary attack surface |
| `python:3.11-alpine` | musl libc incompatible with many Python native extensions (parselmouth, numpy) |
| Full Debian | Too large; unnecessary tools |

## References

- `00_MASTER_PLAN.md §0.3.3` (anti-patterns)
- `04_DEVOPS_LLD.md §Containers`
