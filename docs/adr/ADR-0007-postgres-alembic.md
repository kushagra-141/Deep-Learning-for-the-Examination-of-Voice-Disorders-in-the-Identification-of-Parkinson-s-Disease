# ADR-0007: PostgreSQL + Alembic (prod), SQLite (dev)

- **Status:** Accepted
- **Date:** 2026-05-01
- **Deciders:** @kushagra

## Context

The application needs to persist predictions, batch job state, model metadata, feedback, and audit logs. We need a database that is production-safe but also allows zero-dependency local development.

## Decision

We will use:
- **PostgreSQL 16** in production (via `asyncpg` driver)
- **SQLite** in development (via `aiosqlite` driver)
- **SQLAlchemy 2.0 (async)** as the ORM/query layer
- **Alembic** for schema migrations

The `DATABASE_URL` env var switches between drivers transparently.

## Consequences

- **Good:** PostgreSQL is the safe default for production — ACID, row-level locking, JSONB, proper UUID type.
- **Good:** SQLite + `aiosqlite` means `make dev` requires no Docker or external services — just `uv sync`.
- **Bad:** There are subtle differences between SQLite and PostgreSQL (UUID handling, JSONB vs JSON, `NOW()` vs `CURRENT_TIMESTAMP`) that can mask bugs. Mitigation: integration tests run against both.
- **Risks:** SQLAlchemy async with `asyncpg` requires careful transaction management.

## Alternatives Considered

| Alternative | Reason rejected |
|---|---|
| MongoDB | No strong relational guarantees; joins for analytics are cumbersome |
| MySQL | Less feature-rich than PostgreSQL for JSONB, UUID, advanced types |
| Prisma (Python) | Not mature; SQLAlchemy is the industry standard |

## References

- `00_MASTER_PLAN.md §0.6, §0.7 Decision #3`
- `02_BACKEND_LLD.md §2.5`
