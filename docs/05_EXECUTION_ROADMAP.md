# 05 — Execution Roadmap

> **Audience.** The engineer / agent doing the actual building, in order.
>
> **How to use.** Work tasks **strictly in ID order** within a phase. A task may not start until everything in its `Depends on` list is **completed**. Tick the checkbox in this file as you finish each task — that is the source of truth.
>
> **Conventions.**
> - **ID** format: `P{phase}-{nn}` (e.g., `P1-03`).
> - **Complexity**: S (≤ 1 h), M (1–4 h), L (4–8 h), XL (≥ 8 h).
> - **Files** lists the principal files to create or modify; obvious supporting files (`__init__.py`, etc.) are implied.
> - **Acceptance** is a list of **objective**, runnable checks. If a check is not green, the task is not done.
> - All commands assume repo root unless prefixed.

---

## Phase 0 — Bootstrap

Goal: an empty but production-shaped monorepo with all tooling running green on a no-op.

### [ ] P0-01 — Create monorepo skeleton
- **Depends on:** —
- **Complexity:** S
- **Files:** `.editorconfig`, `.gitattributes`, `.gitignore`, `LICENSE`, `CODEOWNERS`, `README.md`
- **Steps:**
  1. Add `.gitignore` with Python (`__pycache__/`, `*.pyc`, `.venv/`, `*.egg-info`, `.coverage`, `htmlcov/`, `dist/`, `build/`), Node (`node_modules/`, `dist/`, `.vite/`), env (`.env`, `.env.*` except `.env.example`), OS, IDE.
  2. Add `LICENSE` (MIT recommended; revise if research-restricted).
  3. Add `CODEOWNERS` with `* @kushagra`.
  4. Update `README.md` to point to `docs/00_MASTER_PLAN.md`.
- **Acceptance:**
  - `git status` is clean after `make` placeholders run.
  - `wc -l README.md docs/*.md` shows non-empty.

### [ ] P0-02 — Backend tooling skeleton
- **Depends on:** P0-01
- **Complexity:** M
- **Files:** `backend/pyproject.toml`, `backend/uv.lock`, `backend/app/__init__.py`, `backend/app/main.py` (stub), `backend/tests/test_smoke.py`
- **Steps:**
  1. `cd backend && uv init --python 3.11`
  2. Add deps from `01_HLD.md` §1.3 to `pyproject.toml`.
  3. Add tool sections: `[tool.ruff]`, `[tool.mypy]` (strict), `[tool.pytest.ini_options]`.
  4. Stub `app/main.py` with a 1-line FastAPI returning `{"hello":"world"}` on `/`.
  5. Add `tests/test_smoke.py` that asserts `/` returns 200.
- **Acceptance:**
  - `cd backend && uv sync && uv run pytest -q` → 1 passed.
  - `uv run ruff check .` and `uv run mypy app` pass.

### [ ] P0-03 — Frontend tooling skeleton
- **Depends on:** P0-01
- **Complexity:** M
- **Files:** `frontend/package.json`, `frontend/tsconfig.json`, `frontend/vite.config.ts`, `frontend/src/main.tsx`, `frontend/index.html`
- **Steps:**
  1. `cd frontend && npm create vite@latest . -- --template react-ts`
  2. Add Tailwind: `npm i -D tailwindcss@3 postcss autoprefixer && npx tailwindcss init -p` (config from `03_FRONTEND_LLD.md` §3.3.1).
  3. Add deps and devDeps from `01_HLD.md` §1.3.
  4. Set `tsconfig.json` `"strict": true, "noUncheckedIndexedAccess": true`.
  5. Set up ESLint with `@typescript-eslint`, `react-hooks`, `jsx-a11y` and Prettier.
  6. Add a smoke test (`vitest`) that mounts `<App />` and asserts a string.
- **Acceptance:**
  - `npm run dev` serves on `http://localhost:5173`.
  - `npm run lint`, `npm run typecheck`, `npm run test`, `npm run build` all pass.

### [ ] P0-04 — Pre-commit hooks
- **Depends on:** P0-02, P0-03
- **Complexity:** S
- **Files:** `.pre-commit-config.yaml`
- **Acceptance:** `pre-commit run --all-files` exits 0.

### [ ] P0-05 — Makefile
- **Depends on:** P0-02, P0-03
- **Complexity:** S
- **Files:** `Makefile`
- **Acceptance:** `make help` lists every target from `04_DEVOPS_LLD.md` §4.2.1.

### [ ] P0-06 — GitHub Actions: CI
- **Depends on:** P0-02, P0-03
- **Complexity:** M
- **Files:** `.github/workflows/ci.yml`, `.github/dependabot.yml`, `.github/pull_request_template.md`
- **Acceptance:** A PR to `main` triggers CI; all jobs (`lint-be`, `test-be`, `lint-fe`, `test-fe`) green.

### [ ] P0-07 — ADR scaffolding
- **Depends on:** P0-01
- **Complexity:** S
- **Files:** `docs/adr/_template.md`, `docs/adr/ADR-0001-monorepo.md` … `ADR-0012-...` (compact, mirroring `00_MASTER_PLAN.md` §0.12)
- **Acceptance:** Each ADR file exists with `Status: Accepted` and a one-paragraph context/decision/consequences.

---

## Phase 1 — Backend MVP

Goal: a working FastAPI service with all 9 trained models, prediction endpoint, dataset analytics, Postgres persistence, and ≥ 80 % test coverage.

### [ ] P1-01 — Bundle dataset
- **Depends on:** P0-02
- **Complexity:** S
- **Files:** `backend/data/parkinsons.data`, `backend/scripts/seed_dataset.py`
- **Steps:** Place CSV; script verifies SHA-256 and prints row count.
- **Acceptance:** `python -m scripts.seed_dataset` reports `195 rows, 23 cols, sha256=…`.

### [ ] P1-02 — Settings & logging
- **Depends on:** P0-02
- **Complexity:** S
- **Files:** `backend/app/core/config.py`, `backend/app/core/logging.py`, `.env.example`
- **Acceptance:** `python -c "from app.core.config import get_settings; print(get_settings().ENV)"` prints `dev`.

### [ ] P1-03 — DB layer + Alembic
- **Depends on:** P1-02
- **Complexity:** M
- **Files:** `backend/app/db/{base,session}.py`, `backend/app/db/models/*.py`, `backend/alembic.ini`, `backend/alembic/{env.py,versions/...}`, `backend/scripts/seed_dataset.py`
- **Steps:**
  1. Implement all 5 ORM models from `02_BACKEND_LLD.md` §2.5.2 + `01_HLD.md` §1.5.1.
  2. `alembic init alembic`; wire `env.py` to `Base.metadata` and `Settings.DATABASE_URL`.
  3. `alembic revision --autogenerate -m "initial"`.
- **Acceptance:**
  - `alembic upgrade head` succeeds against an empty SQLite file.
  - `pytest tests/integration/test_db_smoke.py` passes (creates a Prediction, queries it back).

### [ ] P1-04 — Pydantic schemas
- **Depends on:** P1-02
- **Complexity:** M
- **Files:** `backend/app/schemas/*.py`
- **Acceptance:** `pytest tests/unit/test_schemas.py` passes (round-trip serialize/deserialize for every schema).

### [ ] P1-05 — Preprocessing service
- **Depends on:** P1-01, P1-04
- **Complexity:** S
- **Files:** `backend/app/services/preprocessing.py`, `tests/unit/test_preprocessing.py`
- **Acceptance:** Test asserts no overlap between `X_train`, `X_test` indices, stratified ratio matches dataset, scaler fit on train only.

### [ ] P1-06 — Trainers
- **Depends on:** P1-05
- **Complexity:** L
- **Files:** `backend/app/services/training.py`, `backend/app/services/evaluation.py`, `tests/unit/test_training.py`
- **Steps:** Implement all 9 trainers + 5-fold CV + calibrated probas (SVM/KNN/DT). Use seed=1 throughout.
- **Acceptance:**
  - `pytest tests/unit/test_training.py` passes for every trainer (returns a fitted estimator with `predict_proba`).
  - Each model's CV mean accuracy ≥ 0.80.

### [ ] P1-07 — Model registry + manager
- **Depends on:** P1-06
- **Complexity:** M
- **Files:** `backend/app/ml/registry.py`, `backend/app/ml/manager.py`, `backend/app/ml/ensemble.py`, `backend/scripts/train.py`, `backend/scripts/verify_models.py`
- **Steps:**
  1. `train.py` orchestrates `seed → split → fit_scaler → train_one for each model → calibrate → evaluate → cv → write joblib + manifest.json`.
  2. `manager.from_dir()` + `verify_integrity()` round-trips OK.
- **Acceptance:**
  - `python -m scripts.train` writes `models/manifest.json` and 9+1 `.joblib` files.
  - `python -m scripts.verify_models` exits 0.
  - Unit test: `ModelManager.predict_proba("lightgbm", x_known)` returns ≈ expected proba ±1e-4.

### [ ] P1-08 — Application factory + middlewares
- **Depends on:** P1-02, P1-04, P1-07
- **Complexity:** M
- **Files:** `backend/app/main.py`, `backend/app/core/{errors.py,rate_limit.py,deps.py,observability.py}`, `backend/app/utils/ids.py`
- **Acceptance:**
  - `uvicorn app.main:app` starts; `GET /api/v1/healthz` returns 200; `GET /api/v1/readyz` returns 200.
  - `X-Request-ID` echoed on every response.

### [ ] P1-09 — Predict router
- **Depends on:** P1-08
- **Complexity:** M
- **Files:** `backend/app/routers/predict.py`, `backend/app/services/prediction.py`, `tests/integration/test_predict_endpoint.py`, `tests/golden/{samples,expected}.jsonl`
- **Acceptance:**
  - `POST /api/v1/predict` returns valid `PredictionResponse` for all 22-feature payloads.
  - `GET /api/v1/predict/sample` returns a valid sample.
  - Integration test passes; golden-sample tolerance ±1e-4.

### [ ] P1-10 — Models router
- **Depends on:** P1-09
- **Complexity:** S
- **Files:** `backend/app/routers/models.py`, `tests/integration/test_models_endpoint.py`
- **Acceptance:** Lists 10 entries (9 + ensemble); each metric endpoint returns the schema in `02_BACKEND_LLD.md` §2.7.5.

### [ ] P1-11 — Analytics router
- **Depends on:** P1-09
- **Complexity:** M
- **Files:** `backend/app/routers/analytics.py`, `backend/app/services/analytics.py`, `tests/integration/test_analytics_endpoint.py`
- **Acceptance:** All four endpoints (`dataset-stats`, `feature/{name}`, `correlation`, `pca`) return well-formed JSON.

### [ ] P1-12 — Explainability
- **Depends on:** P1-09
- **Complexity:** M
- **Files:** `backend/app/services/explainability.py`, `tests/unit/test_shap.py`
- **Acceptance:** For each model, `shap_top_k` returns 5 entries summing (with bias) to ≈ model's logit; tree explainers used where applicable; KernelExplainer cached.

### [ ] P1-13 — Persistence wiring
- **Depends on:** P1-09, P1-03
- **Complexity:** S
- **Files:** `backend/app/repositories/prediction.py`, `tests/integration/test_prediction_persistence.py`
- **Acceptance:** Each `/predict` call writes a `predictions` row + N `model_predictions` rows.

### [ ] P1-14 — Coverage gate
- **Depends on:** P1-09 → P1-13
- **Complexity:** S
- **Acceptance:** `pytest --cov=app --cov-fail-under=80` green.

---

## Phase 2 — Frontend MVP

Goal: a beautiful, accessible Predict + Dashboard + Home + About SPA wired to the backend via auto-generated client. (Audio, batch, explorer, what-if come in Phase 3.)

### [ ] P2-01 — Design system tokens
- **Depends on:** P0-03
- **Complexity:** S
- **Files:** `frontend/src/styles/{tokens.css,globals.css,print.css}`, `frontend/tailwind.config.ts`
- **Acceptance:** Visiting `/` shows correct fonts/colors in light, dark, system; theme switch works.

### [ ] P2-02 — App shell, router, providers
- **Depends on:** P2-01
- **Complexity:** M
- **Files:** `frontend/src/{App,main,routes}.tsx`, `frontend/src/providers/{QueryProvider,ThemeProvider,I18nProvider}.tsx`, `frontend/src/components/layout/{AppShell,TopNav,Footer,ThemeSwitcher}.tsx`, `frontend/src/i18n/{index.ts,en.json}`
- **Acceptance:** Navigating between `/`, `/predict`, `/dashboard`, `/about` works without full reload; lazy chunks visible in network panel; reduced-motion respected.

### [ ] P2-03 — Disclaimer scaffolding
- **Depends on:** P2-02
- **Complexity:** S
- **Files:** `frontend/src/components/disclaimer/*`, `frontend/src/stores/consent.ts`
- **Acceptance:** First visit shows modal, requires acknowledgement, persists; banner visible on every page.

### [ ] P2-04 — Generated API client
- **Depends on:** P1-08, P0-03
- **Complexity:** S
- **Files:** `frontend/src/api/{client.ts,queryKeys.ts,generated/...}`, npm script `gen:api`
- **Acceptance:** `npm run gen:api` produces `src/api/generated/`; `make ci` includes drift check that diffs the generated tree.

### [ ] P2-05 — shadcn primitives
- **Depends on:** P2-01
- **Complexity:** M
- **Files:** `frontend/src/components/ui/*`
- **Acceptance:** Button/Input/Card/Tabs/Tooltip/Dialog/Select/Slider/Accordion/Progress/Badge/Toast all import-clean and render in Storybook-less harness in `tests/components`.

### [ ] P2-06 — HomePage
- **Depends on:** P2-02, P2-04
- **Complexity:** M
- **Files:** `frontend/src/pages/HomePage.tsx`, `frontend/src/components/common/PageHeader.tsx`
- **Acceptance:** Hero + trust strip + how-it-works + live-stats render; CTAs route correctly; Lighthouse ≥ 90.

### [ ] P2-07 — PredictPage (manual flow)
- **Depends on:** P2-04, P2-05, P2-06
- **Complexity:** L
- **Files:** `frontend/src/pages/PredictPage.tsx`, `frontend/src/components/prediction/*`, `frontend/src/lib/schemas/voiceFeatures.ts`, `frontend/src/hooks/usePrediction.ts`
- **Acceptance:**
  - Submitting valid features renders `<ResultCard>` with all 9 model chips + ensemble + SHAP top-5.
  - Sample loader fills the form.
  - Error states (422, 503) show inline errors / toast with `request_id`.
  - Keyboard-only flow works end-to-end.

### [ ] P2-08 — DashboardPage
- **Depends on:** P2-04, P2-05
- **Complexity:** L
- **Files:** `frontend/src/pages/DashboardPage.tsx`, `frontend/src/components/dashboard/*`
- **Acceptance:** All 5 tabs render with real data from BE; each chart has an "Explain" disclosure; charts are responsive.

### [ ] P2-09 — AboutPage
- **Depends on:** P2-02
- **Complexity:** S
- **Files:** `frontend/src/pages/AboutPage.tsx`
- **Acceptance:** Glossary table renders; references link out; limitations section present.

### [ ] P2-10 — E2E happy path
- **Depends on:** P2-07, P2-08
- **Complexity:** M
- **Files:** `frontend/tests/e2e/predict.spec.ts`, `playwright.config.ts`
- **Acceptance:** Test: load `/`, navigate to `/predict`, click "Random sample", submit, assert the result card renders with non-empty per-model strip; passes in CI.

---

## Phase 3 — Premium UX

Goal: the features that elevate the app from "school project" to "premium demo".

### [ ] P3-01 — Backend feature extractor
- **Depends on:** P1-09
- **Complexity:** L
- **Files:** `backend/app/services/feature_extraction.py`, `backend/app/services/nonlinear.py`, `backend/tests/fixtures/audio/*.wav`, `tests/unit/test_feature_extractor.py`
- **Acceptance:** `extract_features_from_audio(<test.wav>)` returns 22-key dict with no NaNs in valid ranges.

### [ ] P3-02 — Audio router
- **Depends on:** P3-01
- **Complexity:** M
- **Files:** `backend/app/routers/audio.py`, `backend/app/schemas/audio.py`, `tests/integration/test_audio_endpoint.py`
- **Acceptance:** `POST /api/v1/audio/predict` (multipart) accepts ≤ 5 MB audio, returns `AudioPredictionResponse` echoing extracted features and prediction; rejects oversize / wrong mime.

### [ ] P3-03 — Audio recorder UI
- **Depends on:** P3-02, P2-07
- **Complexity:** L
- **Files:** `frontend/src/lib/audio/{recorder,waveform,encoder}.ts`, `frontend/src/components/audio/*`, `frontend/src/pages/AudioPage.tsx`, `frontend/src/hooks/useAudioRecorder.ts`
- **Acceptance:** Record → Stop → Submit works in Chrome and Firefox; permission-denied state shown; iOS Safari falls back to file upload.

### [ ] P3-04 — SHAP visualization
- **Depends on:** P2-07
- **Complexity:** M
- **Files:** `frontend/src/components/prediction/ShapWaterfall.tsx`
- **Acceptance:** Waterfall chart shows top-5 by `|shap|`, colored by tone, with feature values; toggling "show all" reveals 22 bars.

### [ ] P3-05 — What-If panel
- **Depends on:** P3-04
- **Complexity:** M
- **Files:** `frontend/src/components/whatif/WhatIfPanel.tsx`, `frontend/src/hooks/useDebouncedValue.ts`
- **Acceptance:** Sliders debounce 250 ms → call `/predict` → gauge animates between values; "reset" works; "apply to form" updates the parent form state.

### [ ] P3-06 — Batch endpoint + page
- **Depends on:** P1-09, P2-07
- **Complexity:** L
- **Files:** `backend/app/routers/batch.py`, `backend/app/services/batch.py`, `backend/app/repositories/batch_job.py`, `frontend/src/pages/BatchPage.tsx`, `frontend/src/components/batch/*`, `tests/integration/test_batch_endpoint.py`, `frontend/tests/e2e/batch.spec.ts`
- **Acceptance:** Upload sample CSV (10 rows) → polling shows progress → CSV download contains 10 rows + new prediction columns.

### [ ] P3-07 — Explorer page
- **Depends on:** P1-11
- **Complexity:** L
- **Files:** `frontend/src/pages/ExplorerPage.tsx`, `frontend/src/components/explorer/*`
- **Acceptance:** PCA scatter, correlation heatmap, feature distribution, dataset table all render; brushing the scatter filters the table.

### [ ] P3-08 — Feedback endpoint + UI
- **Depends on:** P1-09
- **Complexity:** S
- **Files:** `backend/app/routers/feedback.py`, `backend/app/repositories/feedback.py`, `frontend/src/components/prediction/FeedbackButtons.tsx`
- **Acceptance:** Thumb-up/down POSTs `/feedback`; toast confirms; rate-limited.

### [ ] P3-09 — PDF report
- **Depends on:** P3-04
- **Complexity:** M
- **Files:** `frontend/src/lib/pdf/ReportDocument.tsx`, `frontend/src/lib/pdf/styles.ts`
- **Acceptance:** "Download report" button opens a generated PDF in a new tab containing disclaimer + summary + per-model + SHAP + features.

### [ ] P3-10 — Share-link
- **Depends on:** P2-07
- **Complexity:** S
- **Files:** `frontend/src/lib/share.ts`, `frontend/src/components/prediction/ShareLinkButton.tsx`
- **Acceptance:** Copy-link → opening that URL in a fresh window prefills the form (and re-submits if `?auto=1`).

### [ ] P3-11 — Recent predictions store
- **Depends on:** P2-07
- **Complexity:** S
- **Files:** `frontend/src/stores/recent.ts`, `frontend/src/components/common/RecentList.tsx`
- **Acceptance:** Last 10 predictions appear in a sidebar; clicking restores the form state.

---

## Phase 3.5 — LLM Layer

> Reference doc: `06_LLM_INTEGRATION_LLD.md`. Each task assumes Phase 3 is complete and that `app/llm/` is an empty namespace.

### [ ] P3.5-01 — Backend dependencies + secrets scaffolding
- **Depends on:** P3-* complete
- **Complexity:** S
- **Files:** `backend/pyproject.toml` (add `openai`, `sse-starlette`, `tiktoken`), `.env.example` (add `LLM_*`, `GROQ_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`), `backend/app/core/config.py` (extend `Settings` per `06_LLM_INTEGRATION_LLD.md` §6.2.4)
- **Acceptance:**
  - `uv sync` resolves cleanly.
  - `Settings()` loads with the new fields; missing required key in `prod` → startup error with a clear message.
  - Secrets never appear in logs (assert in `tests/unit/test_settings_redaction.py`).

### [ ] P3.5-02 — LLM provider abstraction
- **Depends on:** P3.5-01
- **Complexity:** M
- **Files:** `backend/app/llm/providers/{base,groq,gemini,openrouter}.py`, `tests/unit/llm/test_providers.py`
- **Steps:**
  1. Implement `LLMProvider` Protocol + `ChatMessage`, `ChatChunk`, `ToolDef` per §6.5.2.
  2. Implement `GroqProvider`, `GeminiProvider`, `OpenRouterProvider` using the `openai` SDK with provider-specific `base_url` / `api_key`.
  3. Each provider exposes `stream_chat(...)` returning an `AsyncIterator[ChatChunk]`.
- **Acceptance:**
  - Providers stream a known prompt against a recorded fixture (use `respx` to mock HTTPX) and yield the expected chunk sequence.
  - Tool-call deltas reassembled correctly across chunks.
  - Timeout (`LLM_TIMEOUT_S`) raises `TimeoutError`, not a hang.

### [ ] P3.5-03 — Provider router + circuit breaker
- **Depends on:** P3.5-02
- **Complexity:** M
- **Files:** `backend/app/llm/router.py`, `tests/unit/llm/test_router.py`
- **Acceptance:**
  - On `RateLimitError` / `5xx` from primary, switches to fallback within the same call.
  - After 3 consecutive primary failures, circuit opens for 60 s; subsequent calls go straight to fallback.
  - Successful primary call resets the failure counter.

### [ ] P3.5-04 — Tool registry + concrete tools
- **Depends on:** P1-09 (predict service), P1-11 (analytics), P1-12 (SHAP), P3.5-01
- **Complexity:** L
- **Files:** `backend/app/llm/tools/{__init__,feature,what_if,model,dataset,shap}.py`, `backend/app/llm/glossary.json`, `tests/unit/llm/test_tools.py`
- **Steps:**
  1. Build `ToolRegistry` with `register`, `for_feature`, `execute` per §6.5.4.
  2. Implement all 6 tools from §6.5.10. `simulate_what_if` calls `services.prediction.predict()` **without** persisting.
  3. Validate `simulate_what_if` updates against `VoiceFeatures` ranges; max 5 features per call.
- **Acceptance:**
  - Each tool has at least one happy-path and one validation-failure unit test.
  - JSON schemas conform to OpenAI tool format.
  - `simulate_what_if` does not write to the DB.

### [ ] P3.5-05 — System prompts + output validator
- **Depends on:** P3.5-01
- **Complexity:** M
- **Files:** `backend/app/llm/prompts/{explainer_system,help_system,narrator_system,refusal_template}.md`, `backend/app/llm/help_corpus.md`, `backend/app/llm/validator.py`, `tests/unit/llm/test_output_validator.py`
- **Acceptance:**
  - `output_validator.check(text)` returns `("ok"|"violation", reason)`; rules mirror §6.8.2 denylist.
  - Narrator output missing the mandatory disclaimer is auto-amended.
  - Test corpus of 10 known-bad outputs all flagged; 10 known-good all pass.

### [ ] P3.5-06 — Token budget + response cache
- **Depends on:** P3.5-01
- **Complexity:** M
- **Files:** `backend/app/llm/budget.py`, `backend/app/llm/cache.py`, `tests/integration/llm/test_budget.py`
- **Steps:**
  1. Per-IP per-minute slowapi limit on chat/help/narrate endpoints (counts toward existing limiter).
  2. Daily token bucket in Redis (`llm:tokens:{client_fp}:{yyyymmdd}`); on exceed → 429 with `Retry-After`.
  3. Global ceiling check against `LLM_DAILY_TOKEN_BUDGET`; exceeded → 503 (UI shows graceful unavailable).
  4. Cache: SHA-of-prompt → assistant text, TTL 1 h, ONLY for tool-free turns.
- **Acceptance:**
  - Hammering test exceeds bucket → returns 429.
  - Identical second call (no tool use) returns cached response, observed via no provider call.

### [ ] P3.5-07 — Chat orchestrator
- **Depends on:** P3.5-03, P3.5-04, P3.5-05, P3.5-06
- **Complexity:** L
- **Files:** `backend/app/llm/orchestrator.py`, `tests/integration/llm/test_orchestrator.py`
- **Steps:**
  1. Build `ChatContext` (prediction snapshot, glossary slice, session id, client fingerprint).
  2. Implement the loop per §6.5.5: stream → tool-call → execute → resume → done.
  3. Wire output validator into the final assistant message.
  4. Persist to in-memory + Redis session store with 24 h TTL.
- **Acceptance:**
  - End-to-end test with a `FakeLLMProvider` script: user msg → tool call → tool result → final answer; messages list ordering matches.
  - Forced violation (test prompt) replaced by canned refusal.

### [ ] P3.5-08 — Chat router (SSE endpoint)
- **Depends on:** P3.5-07
- **Complexity:** M
- **Files:** `backend/app/routers/chat.py`, `backend/app/schemas/chat.py`, `tests/integration/llm/test_chat_endpoint.py`
- **Steps:**
  1. Implement `POST /api/v1/chat` returning `EventSourceResponse` of `ChatChunkOut`.
  2. Heart-beat every 15 s while streaming (`:keepalive`).
  3. Validate `ChatRequest`; require `prediction_id` for `feature="explainer"`.
- **Acceptance:**
  - SSE client receives `delta` → `tool` → `delta` → `done` events in order.
  - Aborting the request mid-stream cancels the provider call (verified via `FakeProvider` cancel marker).
  - Rate-limit violations return 429 before opening the stream.

### [ ] P3.5-09 — Help endpoint + corpus
- **Depends on:** P3.5-05, P3.5-06
- **Complexity:** S
- **Files:** `backend/app/routers/help.py`, `backend/app/schemas/help.py`, `tests/integration/llm/test_help_endpoint.py`
- **Acceptance:**
  - `POST /api/v1/help {question}` returns `{answer, used_corpus_section?}`.
  - Off-corpus question returns the canned "outside my docs" response (asserted text).
  - Cache hit observed for repeated identical question.

### [ ] P3.5-10 — Narrate endpoint + DB migration
- **Depends on:** P3.5-07, P1-13 (predictions repo)
- **Complexity:** M
- **Files:** `backend/alembic/versions/20260518_0010_add_narrative.py`, `backend/app/services/narrator.py`, `backend/app/routers/predictions.py` (add `/predictions/{id}/narrate`), `backend/app/schemas/narrate.py`, `tests/integration/llm/test_narrate_endpoint.py`
- **Acceptance:**
  - Migration adds `narrative`, `narrative_model`, `narrative_generated_at` columns.
  - First call generates and persists; second call returns cached row with no provider call (verify via metric).
  - Admin DELETE forces regeneration; non-admin DELETE → 401.
  - Narrator output ≤ 110 words and contains the mandatory disclaimer sentence.

### [ ] P3.5-11 — LLM observability
- **Depends on:** P3.5-08, P3.5-09, P3.5-10
- **Complexity:** S
- **Files:** `backend/app/llm/metrics.py`, `infra/prometheus/prometheus.yml` (add scrape if missing), `infra/grafana/provisioning/dashboards/llm.json`
- **Acceptance:**
  - `/metrics` exposes the counters and histograms in §6.10.
  - Provoking a policy violation produces a Sentry event with the right tags (no PII).
  - Grafana dashboard "LLM" loads with at least 4 panels.

### [ ] P3.5-12 — Frontend `useChatStream` hook + types
- **Depends on:** P3.5-08
- **Complexity:** M
- **Files:** `frontend/src/hooks/useChatStream.ts`, `frontend/src/lib/sse.ts`, `frontend/src/api/chat.ts`, `frontend/src/lib/schemas/chat.ts`, `tests/unit/hooks/useChatStream.test.tsx`
- **Steps:**
  1. SSE parser handles partial JSON across chunks, heartbeats, and aborts.
  2. Hook exposes `{messages, send, stop, status}`; aborts in-flight on unmount.
  3. Types kept in sync with backend schemas via a snapshot test (chat schemas are NOT auto-generated because OpenAPI for SSE is poor).
- **Acceptance:**
  - Vitest with mock `ReadableStream` exercises the four chunk types end-to-end.
  - Stop button aborts within 200 ms (uses `AbortController`).

### [ ] P3.5-13 — `<ChatSidebar>` component
- **Depends on:** P3.5-12, P2-07 (Predict result card)
- **Complexity:** L
- **Files:** `frontend/src/components/llm/{ChatSidebar,ChatMessage,ToolBadge,ChatComposer}.tsx`, `frontend/src/components/prediction/ResultCard.tsx` (add "Discuss this result" button + `Cmd/Ctrl+K` shortcut), `tests/e2e/chat.spec.ts`
- **Acceptance:**
  - Drawer opens via button click or shortcut; focus trapped (Radix Dialog).
  - Tokens stream into the assistant bubble; tool calls render an inline badge.
  - Suggested questions populated from the user's actual prediction.
  - Reduced-motion respected; Lighthouse a11y ≥ 95 on Predict.
  - Playwright spec: open chat, ask suggested question, assert deltas + final reply length > 0.

### [ ] P3.5-14 — `<HelpBot>` floating widget
- **Depends on:** P3.5-09
- **Complexity:** M
- **Files:** `frontend/src/components/llm/HelpBot.tsx`, `frontend/src/hooks/useHelpBot.ts`, mounted in `<AppShell>` (hidden on `/admin/*`)
- **Acceptance:**
  - Floating `?` button visible on Home/Predict/Audio/Dashboard/Explorer/About; not on `/admin/*`.
  - Suggested chips work; off-corpus question shows the canned out-of-docs reply.
  - Persistent disclaimer footer present.

### [ ] P3.5-15 — `<NarratedSummary>` in PDF report
- **Depends on:** P3.5-10, P3-09 (PDF report)
- **Complexity:** S
- **Files:** `frontend/src/lib/pdf/ReportDocument.tsx` (insert narrated paragraph block), `frontend/src/hooks/useReportNarration.ts`, `frontend/src/components/llm/NarratedSummary.tsx`
- **Acceptance:**
  - "Generate report" button shows a spinner while narration loads.
  - On 503, PDF still downloads with a static placeholder.
  - Cached narration doesn't trigger a second LLM call (asserted via network mock).

### [ ] P3.5-16 — LLM eval set + CI gate
- **Depends on:** P3.5-08, P3.5-09, P3.5-10
- **Complexity:** M
- **Files:** `backend/tests/eval/llm_eval.jsonl`, `backend/tests/eval/run_eval.py`, `.github/workflows/llm-eval.yml`
- **Steps:**
  1. Curate 30 `(question, expected_property)` pairs as in §6.11.3 (10 explainer / 10 help / 10 narrator).
  2. Eval script runs against the **real** primary provider with `temperature=0`; uploads JSON results as artifact.
  3. Weekly cron + manual trigger; warns (not fails) PRs if pass rate drops below 95 %.
- **Acceptance:**
  - `python -m tests.eval.run_eval` reports a pass rate; first run ≥ 95 %.
  - Workflow runs successfully against secrets in GH Actions.

### [ ] P3.5-17 — Provider failover smoke test (manual)
- **Depends on:** P3.5-13, P3.5-14, P3.5-15
- **Complexity:** S
- **Acceptance:**
  - Temporarily set `GROQ_API_KEY=invalid` → chat still works (via Gemini fallback); a Sentry event records the primary failure.
  - Restore key; circuit closes after 60 s.
  - Document the test outcome in `docs/runbook.md` under "LLM provider outage".

---

## Phase 4 — Hardening

### [ ] P4-01 — Admin auth (BE)
- **Depends on:** P1-08
- **Complexity:** M
- **Files:** `backend/app/core/security.py`, `backend/app/routers/auth.py`, `backend/app/schemas/auth.py`, `backend/app/core/deps.py` (extend `get_current_admin`)
- **Acceptance:** Login with correct password sets cookie; wrong password returns 401; rate-limited to 5/min/IP; 10 failures lock for 30 min.

### [ ] P4-02 — Admin pages (FE)
- **Depends on:** P4-01
- **Complexity:** M
- **Files:** `frontend/src/pages/{AdminLoginPage,AdminPage}.tsx`, `frontend/src/components/admin/RequireAdmin.tsx`
- **Acceptance:** `/admin` is gated; pagination across predictions / feedback / batch / audit-log works; `noindex` meta present.

### [ ] P4-03 — Rate limiting global
- **Depends on:** P1-08
- **Complexity:** S
- **Acceptance:** Hammer endpoints from a script → confirm 429 after limit; Redis keys observable.

### [ ] P4-04 — Sentry + Prometheus instrumentation
- **Depends on:** P1-08
- **Complexity:** M
- **Files:** `backend/app/core/observability.py` (already stubbed in P1-08), `infra/prometheus/prometheus.yml`
- **Acceptance:** Forcing an exception in dev sends an event to Sentry; `/metrics` includes custom counters; Grafana dashboards (provisioned) load.

### [ ] P4-05 — Frontend E2E suite expansion
- **Depends on:** P3-03, P3-06
- **Complexity:** M
- **Files:** `frontend/tests/e2e/{audio.spec.ts,batch.spec.ts}`
- **Acceptance:** Both specs green in CI matrix (chromium + webkit).

### [ ] P4-06 — Lighthouse + axe gates
- **Depends on:** P3-*, P4-02
- **Complexity:** S
- **Acceptance:** CI step runs Lighthouse on Home/Predict/Audio/Dashboard; fails if < 90; axe violations = 0.

### [ ] P4-07 — Coverage to 90%
- **Depends on:** Phase 3
- **Complexity:** M
- **Acceptance:** `--cov-fail-under=90` green.

### [ ] P4-08 — Security headers / CORS / CSP audit
- **Depends on:** P4-01
- **Complexity:** S
- **Acceptance:** `curl -I` against a deployed dev instance shows all headers from `02_BACKEND_LLD.md` §2.12; Mozilla Observatory grade A.

---

## Phase 5 — Containerize & Deploy

### [ ] P5-01 — Backend Dockerfile (multi-stage, distroless)
- **Depends on:** P4-*
- **Complexity:** M
- **Files:** `backend/Dockerfile`, `backend/.dockerignore`
- **Acceptance:** Image size < 350 MB; `docker run --rm <img>` boots; `trivy image` reports 0 HIGH/CRITICAL.

### [ ] P5-02 — Frontend Dockerfile (nginx)
- **Depends on:** P4-*
- **Complexity:** S
- **Files:** `frontend/Dockerfile`, `frontend/.dockerignore`, `infra/nginx/spa.conf`
- **Acceptance:** Image size < 60 MB; serves SPA on 80; healthcheck passes.

### [ ] P5-03 — Compose files
- **Depends on:** P5-01, P5-02
- **Complexity:** M
- **Files:** `infra/docker/docker-compose.{dev,prod,observability}.yml`, `infra/postgres/init.sql`
- **Acceptance:** `docker compose -f docker-compose.prod.yml up -d` brings up 5 services healthy.

### [ ] P5-04 — Caddy reverse proxy
- **Depends on:** P5-03
- **Complexity:** S
- **Files:** `infra/caddy/Caddyfile`
- **Acceptance:** With a real DNS name, TLS provisioned automatically; `https://<domain>/api/v1/healthz` 200; SSL Labs A+.

### [ ] P5-05 — `images.yml` workflow
- **Depends on:** P5-01, P5-02
- **Complexity:** M
- **Files:** `.github/workflows/images.yml`
- **Acceptance:** Push to `main` produces tagged images on GHCR; manifest artifact uploaded.

### [ ] P5-06 — `setup.sh`, `deploy.sh`, `rollback.sh`
- **Depends on:** P5-03
- **Complexity:** L
- **Files:** `deploy/{setup,deploy,rollback}.sh`
- **Acceptance:** Fresh EC2 → `setup.sh` succeeds → site live; `deploy.sh <sha>` swaps with no downtime; `rollback.sh` reverts.

### [ ] P5-07 — Backups
- **Depends on:** P5-06
- **Complexity:** S
- **Files:** `deploy/{backup,restore}.sh`
- **Acceptance:** A nightly cron writes a dump to S3; `restore.sh` round-trips a snapshot into a fresh DB.

### [ ] P5-08 — (Optional) Terraform
- **Depends on:** P5-06
- **Complexity:** M
- **Files:** `infra/terraform/{main,variables,outputs}.tf`, `infra/terraform/README.md`
- **Acceptance:** `terraform apply` from clean account creates EC2 + EIP + SG + Route 53 record; `outputs` includes the URL.

### [ ] P5-09 — Runbook
- **Depends on:** P5-06
- **Complexity:** S
- **Files:** `docs/runbook.md`
- **Acceptance:** Each row of the table in `04_DEVOPS_LLD.md` §4.10 has been executed at least once and notes added inline.

### [ ] P5-10 — Launch checklist
- **Depends on:** P5-* all
- **Complexity:** S
- **Acceptance:**
  - All P0–P5 boxes ticked.
  - `make ci` green.
  - `https://<domain>` loads, accepts a recording, returns a prediction with SHAP, downloads a PDF.
  - Sentry receives a deliberate test exception with the right release tag.
  - First nightly backup is in S3.
  - Disclaimer modal shows on first visit; persistent banner on every page.

---

## Cross-cutting reminders for the executor
- **Always** run `make lint typecheck test` before opening a PR.
- **Always** regenerate the FE API client when a BE schema changes (`make gen-api`).
- **Never** commit a `.env` file; only `.env.example`.
- **Never** train models inside the runtime image.
- **Never** disable a CI step to land code; fix the cause.
- If you have to deviate from these documents, **add an ADR** under `docs/adr/` first.
