# Parkinson's Voice Detection — Web App

> **Entry point for engineers:** Start by reading [`docs/00_MASTER_PLAN.md`](docs/00_MASTER_PLAN.md).

---

## ⚠️ Medical Disclaimer

> **This tool is a research and educational demonstration. It is NOT a diagnostic device and must not be used to make clinical decisions. Consult a qualified neurologist for any medical concern.**

---

## What is this?

A production-grade full-stack web application that:

1. **Records or accepts an uploaded voice sample** (or accepts 22 manual numeric features)
2. **Extracts acoustic features** server-side using Praat via `parselmouth`
3. **Runs 9 classifiers + an ensemble** trained on the UCI Parkinson's dataset
4. **Returns a probability + SHAP explanation** of which features drove the prediction
5. **Provides a PDF report**, model-comparison dashboard, dataset explorer, and a free-tier LLM assistant grounded in the prediction data

## Quick Links

| Document | Purpose |
|---|---|
| [`docs/00_MASTER_PLAN.md`](docs/00_MASTER_PLAN.md) | Vision, decisions, ADRs, roadmap overview |
| [`docs/01_HLD.md`](docs/01_HLD.md) | Architecture diagrams, tech stack, data flows |
| [`docs/02_BACKEND_LLD.md`](docs/02_BACKEND_LLD.md) | FastAPI backend spec, ML pipeline, endpoints |
| [`docs/03_FRONTEND_LLD.md`](docs/03_FRONTEND_LLD.md) | React frontend spec, design system, components |
| [`docs/04_DEVOPS_LLD.md`](docs/04_DEVOPS_LLD.md) | Docker, CI/CD, infrastructure, runbook |
| [`docs/05_EXECUTION_ROADMAP.md`](docs/05_EXECUTION_ROADMAP.md) | Phase-by-phase build order with acceptance criteria |
| [`docs/06_LLM_INTEGRATION_LLD.md`](docs/06_LLM_INTEGRATION_LLD.md) | Free-tier LLM layer design |
| [`docs/runbook.md`](docs/runbook.md) | Operational runbook (created in Phase 5) |

## Project Structure

```
.
├── backend/          # FastAPI + ML pipeline
├── frontend/         # React 18 + Vite + TypeScript SPA
├── infra/            # Docker Compose, Caddy, Prometheus, Terraform
├── deploy/           # Deployment scripts (setup, deploy, rollback, backup)
├── docs/             # All architecture and planning documents
└── Makefile          # Top-level targets: dev, test, lint, build, ci
```

## Getting Started (Local Development)

```bash
# 1. Clone and enter
git clone <repo-url>
cd <repo-dir>

# 2. Copy and fill environment variables
cp .env.example .env

# 3. Start everything
make dev
```

The app runs at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000/api/v1/docs

## Tech Stack

| Layer | Choice |
|---|---|
| Backend | Python 3.11, FastAPI, SQLAlchemy 2 (async), PostgreSQL / SQLite |
| ML | scikit-learn, LightGBM, XGBoost, SHAP |
| Audio | praat-parselmouth, librosa |
| Frontend | React 18, Vite, TypeScript, Tailwind CSS, shadcn/ui |
| Deployment | Docker Compose, Caddy (auto-TLS), EC2 |
| LLM | Groq (primary) + Gemini (fallback), grounded-only |

See [`docs/00_MASTER_PLAN.md §0.6`](docs/00_MASTER_PLAN.md) for the full rationale behind each choice.

## Dataset

Uses the public [UCI Parkinson's Disease Dataset](https://archive.ics.uci.edu/ml/datasets/Parkinsons) by Little et al. (2007). 195 voice recordings, 22 acoustic features, 147 Parkinson's / 48 healthy subjects.

## License

MIT — see [LICENSE](LICENSE). The UCI dataset is freely available under an open license.
