# ADR-0003: TypeScript strict mode, no plain JSX

- **Status:** Accepted
- **Date:** 2026-05-01
- **Deciders:** @kushagra

## Context

The frontend API client is auto-generated from the backend's OpenAPI schema. If the frontend does not use strict TypeScript, the type safety benefit of codegen is undermined — runtime errors become possible at the API boundary.

## Decision

We will use **TypeScript** throughout the frontend with `tsconfig.json` set to `"strict": true` and `"noUncheckedIndexedAccess": true`. No plain `.jsx` or `.js` files are permitted in `frontend/src/`. The `tsc --noEmit` check is a required CI gate.

## Consequences

- **Good:** End-to-end types from backend schema → generated client → component props prevent the most common UI bugs (undefined access, wrong prop type).
- **Good:** Auto-generated types from `openapi-typescript-codegen` are immediately usable.
- **Bad:** Slightly higher initial boilerplate for developers unfamiliar with strict TS.
- **Risks:** Third-party libraries without type definitions require `@types/` packages or manual declaration files.

## Alternatives Considered

| Alternative | Reason rejected |
|---|---|
| Plain JavaScript | No compile-time safety; defeats the purpose of codegen |
| TypeScript without strict | Type errors still possible; `any` usage unchecked |

## References

- `00_MASTER_PLAN.md §0.6`
- `03_FRONTEND_LLD.md §Tooling`
