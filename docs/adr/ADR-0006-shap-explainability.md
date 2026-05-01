# ADR-0006: SHAP for explainability

- **Status:** Accepted
- **Date:** 2026-05-01
- **Deciders:** @kushagra

## Context

In a medical-adjacent ML application, model explainability is critical. Users (medical students, researchers) need to understand *why* a model predicted Parkinson's. We need a feature-attribution method that works across all 9 model families (tree ensembles, SVM, KNN).

## Decision

We will use **SHAP** (SHapley Additive exPlanations):
- `TreeExplainer` for tree-based models (LightGBM, XGBoost, Random Forest, Decision Tree, Bagging, AdaBoost)
- `KernelExplainer` with a background sample for SVM and KNN

The SHAP top-5 contributions (by absolute value) are returned in the `PredictionResponse` and visualized as a waterfall chart in the frontend.

## Consequences

- **Good:** SHAP values are theoretically grounded (game-theory Shapley values) and sum to the model's output.
- **Good:** `TreeExplainer` is fast (milliseconds per prediction for tree models).
- **Bad:** `KernelExplainer` is slow for SVM/KNN — mitigated by caching per model with `@lru_cache` and using `nsamples=64`.
- **Risks:** KernelExplainer approximation may not be accurate with very small `nsamples`.

## Alternatives Considered

| Alternative | Reason rejected |
|---|---|
| LIME | Less theoretically grounded; inconsistent across runs; slower for tree models |
| Integrated Gradients | Gradient-based; not applicable to non-differentiable models (SVM, KNN, DT) |
| Permutation importance | Global, not per-prediction; slow |

## References

- `00_MASTER_PLAN.md §0.6`
- `02_BACKEND_LLD.md §2.6.9`
- Lundberg & Lee (2017). A Unified Approach to Interpreting Model Predictions. NeurIPS.
