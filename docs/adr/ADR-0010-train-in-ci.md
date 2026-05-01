# ADR-0010: Train models in CI, ship as artifacts

- **Status:** Accepted
- **Date:** 2026-05-01
- **Deciders:** @kushagra

## Context

The original notebook trains models at runtime or inside the Docker image build. This creates several problems: slow builds, non-deterministic results if dependencies change, and a fat image that carries training dependencies (scikit-learn full build, etc.).

## Decision

We will train models **offline in CI** (GitHub Actions), store the resulting `.joblib` files as CI artifacts, and **copy them into the Docker image at build time**. The `backend/scripts/train.py` script is the single source of truth for training.

The runtime Docker image contains only inference dependencies — not training dependencies like `xgboost` build tools, `shap` source, etc.

> **Note:** For the MVP, `shap` and `lightgbm` are also needed at inference time (for SHAP explanations). These are included in the runtime image. The separation is: training data, training loops, and cross-validation code do NOT need to be in the runtime container.

## Consequences

- **Good:** Deterministic builds — the same git SHA always produces the same model.
- **Good:** Runtime image does not need to re-train (startup is fast, no heavy computation on `docker run`).
- **Good:** Training artifacts are versioned with the git SHA via CI.
- **Bad:** Training must be run in CI before images can be built. This adds ~5 min to the CI pipeline.
- **Risks:** If CI is unavailable, models cannot be updated. Mitigation: `make train` still works locally for development.

## Alternatives Considered

| Alternative | Reason rejected |
|---|---|
| Train at Docker build time | Slow builds; non-deterministic; violates `00_MASTER_PLAN.md §0.3.3` |
| Train at container startup | Even worse — adds minutes to every deploy |
| External model registry (MLflow) | Adds infrastructure complexity not justified at this scale |

## References

- `00_MASTER_PLAN.md §0.3.3` (anti-patterns)
- `01_HLD.md §1.4.5` (training pipeline flow)
- `04_DEVOPS_LLD.md §CI/CD`
