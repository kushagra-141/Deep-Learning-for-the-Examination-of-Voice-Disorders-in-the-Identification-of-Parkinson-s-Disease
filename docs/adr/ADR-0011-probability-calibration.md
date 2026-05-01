# ADR-0011: Calibrate probabilities for SVM/KNN/DT

- **Status:** Accepted
- **Date:** 2026-05-01
- **Deciders:** @kushagra

## Context

Raw `predict_proba` from SVM, KNN, and DT are not true probabilities. In a medical-adjacent app, miscalibrated probabilities are misleading.

## Decision

Wrap SVM, KNN, DT with `CalibratedClassifierCV(method="isotonic", cv=5)`, fit on the training set only.

## Consequences

- **Good:** Calibrated probabilities are true probabilities.
- **Bad:** 3 extra `.joblib` files.

## References

- `02_BACKEND_LLD.md §2.6.3`
