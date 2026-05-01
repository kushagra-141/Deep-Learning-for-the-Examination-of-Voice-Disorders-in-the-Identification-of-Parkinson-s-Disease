# ADR-0012: Use joblib instead of pickle

- **Status:** Accepted
- **Date:** 2026-05-01
- **Deciders:** @kushagra

## Context

ML models need to be serialized and deserialized. Python's `pickle` is the default but has known security risks (arbitrary code execution on load).

## Decision

Use `joblib` for all model serialization. At startup, verify SHA-256 of each `.joblib` file against `manifest.json`. The manifest is HMAC-signed in production.

## Consequences

- **Good:** `joblib` is optimized for numpy arrays (mmap, compression). SHA-256 check prevents tampered model files from loading.
- **Bad:** Same deserialization risk as `pickle` if the file is replaced without updating the manifest. Mitigated by read-only volume mounts in Docker.

## References

- `02_BACKEND_LLD.md §2.6.6`
- `00_MASTER_PLAN.md §0.3.3`
