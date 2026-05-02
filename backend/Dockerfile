# syntax=docker/dockerfile:1.4

# ──────────────────────────────────────────────────────────────────────────────
# Single-stage build to minimize disk usage during build on small EC2 instances
# ──────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim-bookworm

# 1. Install system dependencies (build + runtime)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libffi-dev \
    libssl-dev \
    util-linux \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 2. Set working directory
WORKDIR /app

# 3. Copy only dependency files first to leverage cache
COPY pyproject.toml README.md ./

# 4. Install dependencies directly into system python (no venv to save space)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir .

# 5. Copy the rest of the app
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
COPY prestart.sh ./prestart.sh
RUN chmod +x ./prestart.sh

# 6. Set environment variables
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=prod
ENV MODELS_DIR="/app/models"
ENV DATA_DIR="/app/data"
ENV UPLOAD_DIR="/app/data/uploads"

# Expose port
EXPOSE 8000

# Run the application via prestart script
CMD ["./prestart.sh"]
