# 04 — DevOps & Deployment Low-Level Design

> **Audience.** Engineer/agent setting up local dev, CI, infrastructure, container stack, observability, and the release process.
>
> **Acceptance.** A clean Ubuntu 22.04 EC2 with Docker installed runs `bash deploy/setup.sh` and ends up serving HTTPS on a custom domain with the full stack healthy and Sentry events flowing.

---

## 4.1 Repo Layout (top level)

```
.
├── backend/                        # see 02_BACKEND_LLD.md
├── frontend/                       # see 03_FRONTEND_LLD.md
├── infra/
│   ├── caddy/Caddyfile             # reverse proxy + TLS
│   ├── docker/                     # docker-compose files
│   │   ├── docker-compose.dev.yml
│   │   ├── docker-compose.prod.yml
│   │   └── docker-compose.observability.yml
│   ├── postgres/init.sql           # role + db creation, idempotent
│   ├── prometheus/prometheus.yml
│   ├── grafana/provisioning/...
│   └── terraform/                  # optional, opt-in
│       ├── main.tf
│       ├── variables.tf
│       ├── outputs.tf
│       └── README.md
├── deploy/
│   ├── setup.sh                    # first-boot bootstrap on EC2
│   ├── deploy.sh                   # zero-downtime container swap
│   ├── rollback.sh                 # revert to previous image tag
│   ├── backup.sh                   # pg_dump → S3
│   └── restore.sh                  # pull dump from S3 → restore
├── docs/                           # this docs set
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                  # PR: lint, type, test, scan
│   │   ├── images.yml              # main: build & push images
│   │   ├── train-models.yml        # weekly retrain (optional)
│   │   └── codeql.yml              # SAST
│   ├── dependabot.yml
│   └── pull_request_template.md
├── .pre-commit-config.yaml
├── .editorconfig
├── .gitattributes
├── .gitignore
├── LICENSE
├── CODEOWNERS
├── Makefile
├── README.md
└── .env.example
```

---

## 4.2 Local Development

### 4.2.1 Make targets (`Makefile`)
```make
.PHONY: help dev backend-run frontend-run backend-test frontend-test test \
        lint typecheck build train migrate seed gen-api ci

help:
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | awk -F':.*?## ' '{printf "  %-22s %s\n",$$1,$$2}'

dev:           ## Start the dev stack (db, redis, hot-reload BE+FE)
	docker compose -f infra/docker/docker-compose.dev.yml up --build

backend-run:   ## Run BE alone (assumes db+redis up)
	cd backend && uv run uvicorn app.main:app --reload --port 8000

frontend-run:  ## Run FE alone
	cd frontend && npm run dev

train:         ## Train all models from data/parkinsons.data
	cd backend && uv run python -m scripts.train --seed 1 --out models

migrate:       ## Apply DB migrations
	cd backend && uv run alembic upgrade head

seed:          ## Ensure parkinsons.data is present
	cd backend && uv run python -m scripts.seed_dataset

gen-api:       ## Regenerate FE TypeScript client from BE OpenAPI
	cd frontend && npm run gen:api

backend-test:  ## pytest with coverage
	cd backend && uv run pytest --cov=app --cov-report=term-missing

frontend-test: ## vitest
	cd frontend && npm run test

test: backend-test frontend-test ## All tests

lint:          ## Lint everything
	cd backend && uv run ruff check . && uv run ruff format --check .
	cd frontend && npm run lint

typecheck:
	cd backend && uv run mypy app
	cd frontend && npm run typecheck

build:         ## Production build of FE and BE images
	docker compose -f infra/docker/docker-compose.prod.yml build

ci: lint typecheck test ## What CI runs locally
```

### 4.2.2 `infra/docker/docker-compose.dev.yml`
- Postgres + Redis exposed on host (`5432`, `6379`).
- Backend container with `--reload` and source bind-mount.
- Frontend container running `npm run dev` with bind-mount + polling watcher (Windows-friendly).
- No Caddy in dev; FE talks to BE on `localhost:8000`.

### 4.2.3 Pre-commit (`.pre-commit-config.yaml`)
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.6.9
    hooks: [{ id: ruff, args: [--fix] }, { id: ruff-format }]
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.11.2
    hooks: [{ id: mypy, additional_dependencies: ['pydantic>=2'] }]
  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v4.0.0-alpha.8
    hooks: [{ id: prettier, files: \.(ts|tsx|js|jsx|json|md|yml|yaml)$ }]
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks: [{ id: end-of-file-fixer }, { id: trailing-whitespace },
            { id: check-yaml }, { id: check-added-large-files, args: [--maxkb=1024] }]
  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v3.4.0
    hooks: [{ id: conventional-pre-commit, stages: [commit-msg] }]
```

---

## 4.3 Containers

### 4.3.1 Backend Dockerfile (`backend/Dockerfile`)

Multi-stage: builder (full Debian slim) → runtime (distroless).

```dockerfile
# syntax=docker/dockerfile:1.7
ARG PY=3.11

# ---------- builder ----------
FROM python:${PY}-slim AS builder
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential libgomp1 libsndfile1 ffmpeg curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /build
COPY pyproject.toml uv.lock* ./
RUN pip install uv && uv sync --frozen --no-dev
COPY app ./app
COPY scripts ./scripts
COPY alembic ./alembic
COPY alembic.ini ./

# ---------- runtime ----------
FROM gcr.io/distroless/python3-debian12:nonroot AS runtime
WORKDIR /app
ENV PYTHONPATH=/app PYTHONUNBUFFERED=1
COPY --from=builder /build/.venv /app/.venv
COPY --from=builder /build/app /app/app
COPY --from=builder /build/alembic /app/alembic
COPY --from=builder /build/alembic.ini /app/alembic.ini
# models are baked in by CI (see 4.5.2):
COPY --from=builder /build/models /app/models
COPY --from=builder /build/data /app/data
ENV PATH=/app/.venv/bin:$PATH
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
  CMD ["python","-c","import urllib.request,sys;sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/v1/healthz').status==200 else 1)"]
USER nonroot
ENTRYPOINT ["python","-m","uvicorn","app.main:app","--host","0.0.0.0","--port","8000","--workers","2","--proxy-headers","--forwarded-allow-ips","*"]
```

> [!NOTE]
> Distroless lacks a shell, so `HEALTHCHECK` uses `python -c`. The non-root user is uid 65532.

### 4.3.2 Frontend Dockerfile (`frontend/Dockerfile`)

Two-stage: node-build → nginx-alpine.

```dockerfile
# ---------- build ----------
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build  # outputs /app/dist

# ---------- serve ----------
FROM nginx:1.27-alpine AS serve
RUN rm /etc/nginx/conf.d/default.conf
COPY infra/nginx/spa.conf /etc/nginx/conf.d/spa.conf
COPY --from=build /app/dist /usr/share/nginx/html
HEALTHCHECK --interval=10s --timeout=2s --retries=3 \
  CMD wget -qO- http://127.0.0.1/ >/dev/null || exit 1
EXPOSE 80
USER nginx
```

`infra/nginx/spa.conf`:
```nginx
server {
  listen 80;
  server_name _;
  root /usr/share/nginx/html;
  add_header X-Content-Type-Options nosniff always;
  add_header Referrer-Policy strict-origin-when-cross-origin always;

  location ~* \.(js|css|woff2|svg|png|webp|ico)$ {
    expires 1y;
    add_header Cache-Control "public, immutable" always;
    try_files $uri =404;
  }
  location / {
    try_files $uri /index.html;
    add_header Cache-Control "no-cache" always;
  }
}
```

### 4.3.3 Image policy
- Both images run as **non-root**.
- Both have `HEALTHCHECK`.
- Both built in CI; never built on the EC2 host.
- Tags: `:sha-<7-char>` (immutable) and `:latest` (mutable; moved manually after smoke).
- Images pushed to **GHCR** (`ghcr.io/<owner>/parkinsons-{api,web}`).

---

## 4.4 Compose Files

### 4.4.1 `infra/docker/docker-compose.prod.yml`
```yaml
name: parkinsons
services:
  caddy:
    image: caddy:2-alpine
    restart: unless-stopped
    ports: ["80:80","443:443"]
    volumes:
      - ../caddy/Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
      - caddy_config:/config
    depends_on: [web, api]

  web:
    image: ghcr.io/${OWNER}/parkinsons-web:${IMAGE_TAG:-latest}
    restart: unless-stopped
    expose: ["80"]
    depends_on: [api]

  api:
    image: ghcr.io/${OWNER}/parkinsons-api:${IMAGE_TAG:-latest}
    restart: unless-stopped
    expose: ["8000"]
    env_file: [../../.env]
    depends_on: [postgres, redis]
    volumes:
      - ../../data:/app/data:ro       # bundled CSV
      # models/ is baked into the image; no mount

  postgres:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - pg_data:/var/lib/postgresql/data
      - ../postgres/init.sql:/docker-entrypoint-initdb.d/00-init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER}"]
      interval: 10s
      timeout: 3s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: ["redis-server", "--save", "60", "1", "--loglevel", "warning"]
    volumes: [redis_data:/data]
    healthcheck: { test: ["CMD","redis-cli","ping"], interval: 10s, timeout: 3s, retries: 5 }

volumes:
  pg_data: {}
  redis_data: {}
  caddy_data: {}
  caddy_config: {}
```

### 4.4.2 `infra/caddy/Caddyfile`
```
{
    email {$ACME_EMAIL}
}

{$DOMAIN} {
    encode zstd gzip
    header {
        Strict-Transport-Security "max-age=63072000; includeSubDomains; preload"
        X-Content-Type-Options nosniff
        X-Frame-Options DENY
        Referrer-Policy strict-origin-when-cross-origin
        Permissions-Policy "microphone=(self), camera=(), geolocation=()"
        Content-Security-Policy "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self' https://o0.ingest.sentry.io; font-src 'self'"
        -Server
    }

    # API + metrics behind /api and /metrics
    @api path /api/* /metrics
    handle @api {
        reverse_proxy api:8000 {
            header_up X-Request-ID {http.request.header.X-Request-ID}
        }
    }

    # Frontend
    handle {
        reverse_proxy web:80
    }

    # Body limits per route — safety in depth (BE also enforces)
    request_body /api/v1/audio/* {
        max_size 5MB
    }
    request_body /api/v1/batch {
        max_size 2MB
    }
}
```

> [!NOTE]
> `{$DOMAIN}` and `{$ACME_EMAIL}` are read from the host environment passed to the `caddy` service.

---

## 4.5 CI / CD

### 4.5.1 `.github/workflows/ci.yml` (runs on PR)

Jobs:
1. **lint-be**: `ruff check`, `ruff format --check`, `mypy app`.
2. **test-be**: spins up Postgres service container, runs `alembic upgrade head` + `pytest --cov=app --cov-fail-under=80`.
3. **lint-fe**: `npm ci`, `npm run lint`, `npm run typecheck`.
4. **test-fe**: `npm run test -- --run`.
5. **api-contract-check**: starts BE in background, regenerates the FE client, fails if `git diff` is non-empty.
6. **scan**: `trivy fs --severity HIGH,CRITICAL .` and `pip-audit`, `npm audit --audit-level=high`.
7. **e2e** (matrix: chromium/webkit): builds containers, brings up `docker-compose.dev.yml`, runs Playwright.
8. **bundle-budget**: builds FE, asserts `dist/assets/index-*.js` gzipped ≤ 250 KB.

All required for merge.

### 4.5.2 `.github/workflows/images.yml` (on push to main)

Steps:
1. Checkout.
2. Set up Python; **train models** (`python -m scripts.train --seed 1 --out backend/models`); upload `manifest.json` + `*.joblib` as artifact.
3. `docker buildx` build of `backend/Dockerfile` (which COPYs `backend/models` into the image), tag `:sha`, `:latest`.
4. `docker buildx` build of `frontend/Dockerfile`, tag `:sha`, `:latest`.
5. Push both to GHCR.
6. Optional: trigger SSH deploy (`appleboy/ssh-action`) only if `Deploy=true` label was on the merged PR.

### 4.5.3 `.github/workflows/codeql.yml`
Standard CodeQL on `python` and `javascript`.

### 4.5.4 `.github/workflows/train-models.yml` (weekly cron, optional)
- Same training step as `images.yml` but opens an automated PR adjusting `manifest.json` and committing new model artifacts (uses `peter-evans/create-pull-request`). Models are stored in the PR branch only — they're deliberately small (a few MB total).

### 4.5.5 Branch protection
- `main` requires: ci + scan + e2e green; ≥ 1 approval; no force-push; signed commits encouraged.

---

## 4.6 Infrastructure

### 4.6.1 Path A — Manual EC2 (default)
- Recommended: `t3.small` (2 vCPU, 2 GB), Ubuntu 22.04 LTS, 16 GB gp3.
- Security group: 22 (your IP only), 80 + 443 (0.0.0.0/0).
- Elastic IP attached.
- Allocate a Route 53 (or external DNS) A record → EIP.
- DNS must resolve **before** Caddy starts (otherwise ACME fails).

### 4.6.2 `deploy/setup.sh`
First-boot bootstrap (idempotent):
1. `apt-get update && apt-get install -y curl git unattended-upgrades ufw`.
2. Install Docker (official convenience script), add `ubuntu` to `docker` group.
3. `ufw allow 22/tcp; ufw allow 80/tcp; ufw allow 443/tcp; ufw enable`.
4. Configure `unattended-upgrades` for security updates only.
5. `git clone <repo>` to `/opt/parkinsons`.
6. Prompt operator for: `DOMAIN`, `ACME_EMAIL`, `OWNER`, `IMAGE_TAG`, `POSTGRES_PASSWORD`, `JWT_SECRET`, `ADMIN_PASSWORD_HASH`, `SENTRY_DSN` → write `.env` in repo root.
7. `docker login ghcr.io` (PAT-based; instructions printed).
8. `docker compose -f infra/docker/docker-compose.prod.yml pull`.
9. `docker compose -f infra/docker/docker-compose.prod.yml up -d`.
10. Wait for `/api/v1/readyz` to return 200; print success message with the URL.
11. Install daily cron for `deploy/backup.sh`.
12. Print instructions for `deploy/deploy.sh` and `rollback.sh`.

### 4.6.3 `deploy/deploy.sh`
Usage: `./deploy.sh <git-sha>`.
- Pulls `:sha-<git-sha>` from GHCR.
- Updates `.env` `IMAGE_TAG=sha-<git-sha>`.
- `docker compose pull web api && docker compose up -d --no-deps web api`.
- Waits for healthcheck; if not healthy in 60 s, `rollback.sh` is invoked automatically with the previous tag (recorded in `.env.previous`).

### 4.6.4 `deploy/rollback.sh`
- Reads `.env.previous` for the prior `IMAGE_TAG`.
- Same pull + up flow as `deploy.sh`.

### 4.6.5 `deploy/backup.sh` (cron daily 03:00 UTC)
```bash
#!/usr/bin/env bash
set -euo pipefail
TS=$(date -u +%Y%m%dT%H%M%SZ)
docker compose -f /opt/parkinsons/infra/docker/docker-compose.prod.yml exec -T postgres \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" \
  | gzip -9 \
  | aws s3 cp - "s3://$BACKUP_BUCKET/postgres/${TS}.sql.gz"
```
S3 lifecycle: 30 days standard, 365 days glacier, then expire.

### 4.6.6 `deploy/restore.sh`
- `aws s3 ls s3://$BACKUP_BUCKET/postgres/ | tail` to pick a dump.
- `gunzip -c | docker compose exec -T postgres psql -U $POSTGRES_USER $POSTGRES_DB`.

### 4.6.7 Path B — Optional Terraform (`infra/terraform/`)
- Resources: `aws_vpc` (default OK), `aws_security_group`, `aws_eip`, `aws_instance`, `aws_route53_record`, `aws_s3_bucket` for backups, `aws_ssm_parameter` for secrets.
- `user_data` runs `curl <repo>/deploy/setup.sh | bash`.
- README in the same folder covers `terraform init && plan && apply`.

---

## 4.7 Secrets & Configuration

| Where | What |
|---|---|
| `.env` (gitignored) | Compose-time vars: `OWNER`, `IMAGE_TAG`, `DOMAIN`, `ACME_EMAIL`, `POSTGRES_*`. |
| AWS SSM Parameter Store | App secrets in prod: `JWT_SECRET`, `ADMIN_PASSWORD_HASH`, `SENTRY_DSN`, `HASH_DAILY_SALT`. Fetched on boot by `setup.sh` and written into `.env`. |
| GitHub Actions secrets | `GHCR_PAT`, `SSH_PRIVATE_KEY`, `EC2_HOST`. |
| Frontend | Build-time `VITE_API_BASE_URL` only. **No secrets** in client code. |

Rotation:
- `HASH_DAILY_SALT`: rotated by a cron in the `api` container (writes a new value daily via SSM and reloads).
- `ADMIN_PASSWORD_HASH`: changed by re-running `setup.sh --rotate-admin`.

---

## 4.8 Observability

### 4.8.1 Logs
- All containers log JSON to stdout.
- `docker compose logs --tail=200 -f api` for live tail.
- Phase 5+: ship to Loki via the Loki Docker driver (one config block per service).

### 4.8.2 Metrics
- BE exposes `/metrics`. Caddy exposes `/metrics` on port 2019 internally (not published).
- Optional `infra/docker/docker-compose.observability.yml` brings up Prometheus + Grafana on a `127.0.0.1`-only port for an SSH-tunnel-only dashboard.
- Prometheus scrapes `api:8000/metrics`.
- Provisioned Grafana dashboards: "API health", "Predictions", "Audio extraction latency", "DB connections".

### 4.8.3 Errors
- Sentry initialized with `release=$(git rev-parse --short HEAD)` baked into the image as `SENTRY_RELEASE`.
- PII scrubbing on; `before_send` strips `features` payloads beyond shape info.

### 4.8.4 Alerts (Phase 5+)
- Uptime monitor (UptimeRobot or Better Stack) hits `/api/v1/healthz` every minute.
- Page on-call (you) on 3 consecutive failures.

---

## 4.9 Security & Compliance

### 4.9.1 Threat-model summary
| Threat | Vector | Mitigation |
|---|---|---|
| RCE via malicious model file | Pickle load | Models built only by CI; SHA-256 verified on load; manifest HMAC-signed in prod. |
| DoS via huge audio uploads | Upload endpoint | Caddy `request_body 5MB` + BE Pydantic limit + per-IP rate-limit. |
| Brute-force admin login | `/auth/login` | slowapi 5/min/IP + 30-minute lock after 10 failures (Redis counter). |
| XSS | User-supplied content (feedback) | All user content rendered as text; CSP forbids inline scripts. |
| CSRF on `/auth/login` | Cross-origin POST | `SameSite=Strict` cookie; CORS locked to `PUBLIC_BASE_URL`. |
| Dependency CVEs | npm/pip | Dependabot weekly + `npm audit`/`pip-audit` in CI. |
| Image CVEs | Base images | Trivy in CI; rebuild on base bumps. |
| Secrets in git | Misconfig | `gitleaks` in pre-commit + GitHub secret scanning. |
| Privacy leakage of PHI | User uploads | Persistent disclaimer, no audio retention without explicit consent, hashed fingerprint only, no IP storage. |

### 4.9.2 Compliance posture
- **Not HIPAA covered.** Disclaimers state this explicitly. Public dataset only.
- **GDPR posture:** no personal data is collected; cookies used only for admin auth (functional, exempt from consent banner).
- **Data subject rights:** `/admin` provides a "purge predictions older than N days" action; default 90 days.

### 4.9.3 Required visible disclaimers
1. **Persistent footer banner** on every page: *"Research/educational use only. Not a diagnostic device."*
2. **First-visit modal** that requires acknowledgement before any prediction action is enabled.
3. **Per-result strip** inside `<ResultCard>` repeating the disclaimer text.
4. **PDF report** front-page disclaimer in 16pt bold.

---

## 4.10 Runbook (`docs/runbook.md` — write during Phase 5)

Common scenarios with exact commands:

| Scenario | Commands |
|---|---|
| Deploy a new SHA | `ssh ec2 "cd /opt/parkinsons && ./deploy/deploy.sh <sha>"` |
| Rollback | `ssh ec2 "cd /opt/parkinsons && ./deploy/rollback.sh"` |
| Tail API logs | `ssh ec2 "cd /opt/parkinsons && docker compose -f infra/docker/docker-compose.prod.yml logs -f --tail=200 api"` |
| Restart API only | `... compose restart api` |
| Trigger backup now | `ssh ec2 "/opt/parkinsons/deploy/backup.sh"` |
| Restore latest dump | `ssh ec2 "/opt/parkinsons/deploy/restore.sh"` (interactive) |
| Disk filling up | `docker system prune -af --volumes` (after taking a backup) |
| Caddy cert renewal failure | `docker compose logs caddy` → check DNS resolves; verify ports 80/443 open. |
| BE 503 readiness | Most likely a model integrity failure → `docker compose logs api` for stack; rebuild image. |
| DB connection pool exhausted | Check `pg_stat_activity`; adjust `DB_POOL_SIZE` and restart. |
| Sentry quota exceeded | Bump retention or sample rate via Sentry UI; not a code change. |

---

## 4.11 Cost Estimate (steady-state)

| Item | Monthly cost (USD, approx.) |
|---|---|
| EC2 `t3.small` 24/7 | ~ $15 |
| EBS 16 GB gp3 | ~ $2 |
| Elastic IP (attached) | $0 |
| Route 53 hosted zone | $0.50 |
| S3 backups (~ 1 GB) | < $0.10 |
| Sentry free tier | $0 |
| GHCR | $0 (public) |
| **Total** | **≈ $18 / mo** |

Bumping to `t3.medium` for headroom: ~ $33/mo.

---

## 4.12 Definition of Done for DevOps

- `make ci` passes locally.
- A push to `main` triggers `images.yml`; both images appear in GHCR within ~10 min.
- A manual `deploy/deploy.sh` against EC2 brings up the new image with zero downtime (Caddy reloads cleanly).
- `https://<domain>` returns the SPA over TLS A+ (test with `ssllabs.com`).
- `https://<domain>/api/v1/healthz` returns 200; Sentry receives a test exception.
- Daily `pg_dump` lands in S3.
- Runbook is published and a dry-run rollback works.
