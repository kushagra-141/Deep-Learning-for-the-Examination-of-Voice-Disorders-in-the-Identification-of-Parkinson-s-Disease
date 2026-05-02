# syntax=docker/dockerfile:1.4

# ──────────────────────────────────────────────────────────────────────────────
# Ultra-compact single-layer build for extremely small EC2 instances
# ──────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim-bookworm

WORKDIR /app

# Copy only dependency files first
COPY pyproject.toml README.md ./

# Install build tools, audio libraries, and PURGE build tools in a single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libffi-dev \
    libssl-dev \
    util-linux \
    libgomp1 \
    ffmpeg \
    libsndfile1 \
    && pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir . \
    && apt-get purge -y build-essential cmake libffi-dev libssl-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Copy the rest of the app
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
COPY prestart.sh ./prestart.sh
RUN chmod +x ./prestart.sh

# Set environment variables
ENV PYTHONPATH="/app"
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=prod
ENV MODELS_DIR="/app/models"
ENV DATA_DIR="/app/data"
ENV UPLOAD_DIR="/app/data/uploads"

EXPOSE 8000
CMD ["./prestart.sh"]
