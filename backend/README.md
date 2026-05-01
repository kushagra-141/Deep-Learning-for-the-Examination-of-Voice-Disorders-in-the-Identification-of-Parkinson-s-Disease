# Parkinson's Voice Detection API — Backend

This is the FastAPI backend for the Parkinson's Voice Detection web application.

## Quick Start

```bash
# Install dependencies (with uv — recommended)
pip install uv
uv sync --extra dev

# Or with pip + venv
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Run the development server
uvicorn app.main:app --reload --port 8000

# Run tests
pytest -q

# Lint
ruff check .
ruff format --check .

# Type check
mypy app
```

## Directory Structure

```
backend/
├── app/               # Application code
│   ├── core/          # Config, logging, observability, security
│   ├── db/            # SQLAlchemy models, sessions, base
│   ├── ml/            # Model registry, manager, ensemble
│   ├── repositories/  # Data access layer
│   ├── routers/       # HTTP layer (thin)
│   ├── schemas/       # Pydantic v2 DTOs
│   ├── services/      # Business logic (framework-agnostic)
│   └── main.py        # Application factory
├── scripts/           # CLI scripts (train, verify_models, seed_dataset)
├── tests/             # pytest tests
│   ├── unit/
│   ├── integration/
│   └── golden/
├── alembic/           # Database migrations
├── data/              # Bundled dataset (parkinsons.data)
└── models/            # Trained model artifacts (populated by scripts/train.py)
```

## See Also

- [Architecture Overview](../docs/01_HLD.md)
- [Backend LLD](../docs/02_BACKEND_LLD.md)
- [Execution Roadmap](../docs/05_EXECUTION_ROADMAP.md)
