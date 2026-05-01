# ADR-0005: parselmouth for audio feature extraction

- **Status:** Accepted
- **Date:** 2026-05-01
- **Deciders:** @kushagra

## Context

The UCI Parkinson's dataset uses features from the Kay Elemetrics Multi-Dimensional Voice Program (MDVP). To accept audio input and extract compatible features, we need a library that produces MDVP-family acoustic features: fundamental frequency (Fo), jitter, shimmer, HNR, etc.

## Decision

We will use **`praat-parselmouth`** — the official Python bindings to Praat — for feature extraction. The feature extraction pipeline is in `backend/app/services/feature_extraction.py`. Nonlinear features (RPDE, DFA, spread1/2, D2, PPE) are implemented separately in `app/services/nonlinear.py` using `nolds` and ported algorithms from the Little (2008) paper.

## Consequences

- **Good:** Produces the same MDVP feature family the dataset uses, ensuring compatibility.
- **Good:** Praat is the gold-standard acoustic analysis tool used in speech pathology research.
- **Bad:** `parselmouth` can be difficult to build in slim Docker base images (requires native compilation).
- **Risks:** Nonlinear features require custom implementations — see risk R-04 in the master plan.

## Alternatives Considered

| Alternative | Reason rejected |
|---|---|
| librosa only | Does not produce MDVP jitter/shimmer/HNR directly; feature mismatch |
| openSMILE | Large binary dependency; harder to install; LGPL license |
| Custom DSP | Too much development time; error-prone |

## References

- `00_MASTER_PLAN.md §0.6, Risk Register R-04`
- `02_BACKEND_LLD.md §2.6.5`
- Little, M.A. et al. (2008). Suitability of Dysphonia Measurements for Telemonitoring of Parkinson's Disease. IEEE Trans. Biomed. Eng.
