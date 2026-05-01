# ══════════════════════════════════════════════════════════════════════════════
# Makefile — Parkinson's Voice Detection Web App
#
# Usage:  make <target>
# All commands assume repo root unless prefixed.
# ══════════════════════════════════════════════════════════════════════════════

.DEFAULT_GOAL := help
SHELL := /bin/bash

# ── Colours ───────────────────────────────────────────────────────────────────
BOLD  := $(shell tput bold 2>/dev/null || echo "")
RESET := $(shell tput sgr0 2>/dev/null || echo "")
CYAN  := $(shell tput setaf 6 2>/dev/null || echo "")
GREEN := $(shell tput setaf 2 2>/dev/null || echo "")

# ── Python environment ────────────────────────────────────────────────────────
PYTHON      := python
UV          := uv
BE_DIR      := backend
FE_DIR      := frontend

# Detect uv vs pip+venv
ifneq ($(shell command -v uv 2>/dev/null),)
  PY_RUN := cd $(BE_DIR) && uv run
  PY_SYNC := cd $(BE_DIR) && uv sync --extra dev
else
  PY_RUN := cd $(BE_DIR) && .venv/bin/python -m
  PY_SYNC := cd $(BE_DIR) && python -m venv .venv && .venv/bin/pip install -e ".[dev]"
endif

# ── Help ──────────────────────────────────────────────────────────────────────
.PHONY: help
help: ## Show this help message
	@echo ""
	@echo "$(BOLD)Parkinson's Voice Detection — Make Targets$(RESET)"
	@echo ""
	@echo "$(CYAN)━━━ Development ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-25s$(RESET) %s\n", $$1, $$2}'
	@echo ""

# ══════════════════════════════════════════════════════════════════════════════
# ── Top-level targets ─────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

.PHONY: dev
dev: ## Start backend + frontend in dev mode (runs both concurrently)
	@echo "$(BOLD)Starting dev servers...$(RESET)"
	@trap 'kill 0' SIGINT; \
		$(MAKE) backend-run & \
		$(MAKE) frontend-run & \
		wait

.PHONY: test
test: backend-test frontend-test ## Run all tests (backend + frontend)

.PHONY: lint
lint: backend-lint frontend-lint ## Run all linters (backend + frontend)

.PHONY: typecheck
typecheck: backend-typecheck frontend-typecheck ## Run all type checkers

.PHONY: build
build: backend-build frontend-build ## Build production artefacts

.PHONY: ci
ci: install lint typecheck test ## Full CI pipeline (install + lint + typecheck + test)

.PHONY: install
install: backend-install frontend-install ## Install all dependencies

# ══════════════════════════════════════════════════════════════════════════════
# ── Backend ───────────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

.PHONY: backend-install
backend-install: ## Install backend Python dependencies
	@echo "$(CYAN)Installing backend dependencies...$(RESET)"
	$(PY_SYNC)

.PHONY: backend-run
backend-run: ## Start the FastAPI development server (port 8000)
	@echo "$(CYAN)Starting FastAPI dev server on http://localhost:8000$(RESET)"
	cd $(BE_DIR) && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

.PHONY: backend-test
backend-test: ## Run backend pytest suite
	@echo "$(CYAN)Running backend tests...$(RESET)"
	$(PY_RUN) pytest -v

.PHONY: backend-test-cov
backend-test-cov: ## Run backend tests with coverage report
	$(PY_RUN) pytest --cov=app --cov-report=html --cov-report=term-missing

.PHONY: backend-test-cov-gate
backend-test-cov-gate: ## Run backend tests with 80% coverage gate
	$(PY_RUN) pytest --cov=app --cov-fail-under=80

.PHONY: backend-lint
backend-lint: ## Run Ruff linter + formatter check on backend
	@echo "$(CYAN)Linting backend (ruff)...$(RESET)"
	cd $(BE_DIR) && $(UV) run ruff check . || cd $(BE_DIR) && python -m ruff check .
	cd $(BE_DIR) && $(UV) run ruff format --check . || cd $(BE_DIR) && python -m ruff format --check .

.PHONY: backend-lint-fix
backend-lint-fix: ## Auto-fix Ruff lint issues
	cd $(BE_DIR) && $(UV) run ruff check --fix . && $(UV) run ruff format .

.PHONY: backend-typecheck
backend-typecheck: ## Run mypy strict type checking on backend
	@echo "$(CYAN)Type-checking backend (mypy)...$(RESET)"
	cd $(BE_DIR) && $(UV) run mypy app || cd $(BE_DIR) && python -m mypy app

.PHONY: backend-build
backend-build: ## Build the backend wheel (for CI artefact upload)
	cd $(BE_DIR) && python -m build

.PHONY: train
train: ## Train all 9 ML models and write models/manifest.json
	@echo "$(CYAN)Training ML models...$(RESET)"
	cd $(BE_DIR) && $(UV) run python -m scripts.train

.PHONY: verify-models
verify-models: ## Verify SHA-256 integrity of all model artifacts
	cd $(BE_DIR) && $(UV) run python -m scripts.verify_models

.PHONY: seed-dataset
seed-dataset: ## Ensure parkinsons.data is present and valid
	cd $(BE_DIR) && $(UV) run python -m scripts.seed_dataset

.PHONY: db-migrate
db-migrate: ## Run Alembic migrations (upgrade head)
	cd $(BE_DIR) && $(UV) run alembic upgrade head

.PHONY: db-migrate-create
db-migrate-create: ## Create a new Alembic migration (usage: make db-migrate-create MSG="description")
	cd $(BE_DIR) && $(UV) run alembic revision --autogenerate -m "$(MSG)"

.PHONY: db-migrate-downgrade
db-migrate-downgrade: ## Downgrade one migration step
	cd $(BE_DIR) && $(UV) run alembic downgrade -1

# ══════════════════════════════════════════════════════════════════════════════
# ── Frontend ──────────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

.PHONY: frontend-install
frontend-install: ## Install frontend npm dependencies
	@echo "$(CYAN)Installing frontend dependencies...$(RESET)"
	cd $(FE_DIR) && npm install

.PHONY: frontend-run
frontend-run: ## Start the Vite dev server (port 5173)
	@echo "$(CYAN)Starting Vite dev server on http://localhost:5173$(RESET)"
	cd $(FE_DIR) && npm run dev

.PHONY: frontend-test
frontend-test: ## Run Vitest unit tests
	@echo "$(CYAN)Running frontend unit tests...$(RESET)"
	cd $(FE_DIR) && npm test

.PHONY: frontend-test-e2e
frontend-test-e2e: ## Run Playwright E2E tests
	cd $(FE_DIR) && npm run test:e2e

.PHONY: frontend-lint
frontend-lint: ## Run ESLint + Prettier check on frontend
	@echo "$(CYAN)Linting frontend (ESLint + Prettier)...$(RESET)"
	cd $(FE_DIR) && npm run lint
	cd $(FE_DIR) && npm run format:check

.PHONY: frontend-lint-fix
frontend-lint-fix: ## Auto-fix ESLint + Prettier issues
	cd $(FE_DIR) && npm run lint:fix && npm run format

.PHONY: frontend-typecheck
frontend-typecheck: ## Run tsc --noEmit on frontend
	@echo "$(CYAN)Type-checking frontend (tsc)...$(RESET)"
	cd $(FE_DIR) && npm run typecheck

.PHONY: frontend-build
frontend-build: ## Build the frontend production bundle
	@echo "$(CYAN)Building frontend...$(RESET)"
	cd $(FE_DIR) && npm run build

.PHONY: dump-openapi
dump-openapi: ## Dump the FastAPI OpenAPI schema to frontend/openapi.json
	@echo "$(CYAN)Dumping OpenAPI schema...$(RESET)"
	cd $(BE_DIR) && $(UV) run python -m scripts.dump_openapi

.PHONY: gen-api
gen-api: dump-openapi ## Regenerate the TypeScript API client from openapi.json
	@echo "$(CYAN)Generating API client from OpenAPI spec...$(RESET)"
	cd $(FE_DIR) && npm run gen:api

.PHONY: check-api-drift
check-api-drift: gen-api ## Fail if openapi.json or generated client has uncommitted changes
	@git diff --exit-code $(FE_DIR)/openapi.json $(FE_DIR)/src/api/generated/ || \
		(echo "$(BOLD)ERROR: API surface is out of sync. Run 'make gen-api' and commit.$(RESET)" && exit 1)

# ══════════════════════════════════════════════════════════════════════════════
# ── Docker / Infra ────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

.PHONY: docker-build
docker-build: ## Build production Docker images (backend + frontend)
	docker compose -f infra/docker/docker-compose.prod.yml build

.PHONY: docker-up
docker-up: ## Start all services in Docker (production compose)
	docker compose -f infra/docker/docker-compose.prod.yml up -d

.PHONY: docker-down
docker-down: ## Stop all Docker services
	docker compose -f infra/docker/docker-compose.prod.yml down

.PHONY: docker-logs
docker-logs: ## Follow logs for all services
	docker compose -f infra/docker/docker-compose.prod.yml logs -f

.PHONY: docker-dev
docker-dev: ## Start services in Docker (dev compose — includes hot reload)
	docker compose -f infra/docker/docker-compose.dev.yml up

# ══════════════════════════════════════════════════════════════════════════════
# ── Cleanup ───────────────────────────────────────────────────────────────────
# ══════════════════════════════════════════════════════════════════════════════

.PHONY: clean
clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf backend/.coverage backend/htmlcov backend/.pytest_cache backend/.mypy_cache backend/.ruff_cache
	rm -rf frontend/dist frontend/coverage frontend/.vite
	@echo "$(GREEN)Clean complete.$(RESET)"

.PHONY: pre-commit-install
pre-commit-install: ## Install pre-commit hooks into .git
	pre-commit install --hook-type pre-commit --hook-type commit-msg

.PHONY: pre-commit-run
pre-commit-run: ## Run pre-commit on all files
	pre-commit run --all-files
