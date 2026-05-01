# syntax=docker/dockerfile:1.4

# ──────────────────────────────────────────────────────────────────────────────
# Stage 1: Build
# ──────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim-bookworm AS builder

# Install system dependencies required for native extensions (numpy, parselmouth, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Set up virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip and install build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel build

# Set working directory
WORKDIR /app

# Copy the dependency specification
COPY pyproject.toml README.md ./
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

# Build the wheel and install dependencies
RUN pip install --no-cache-dir .

# ──────────────────────────────────────────────────────────────────────────────
# Stage 2: Runtime (Slim)
# ──────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim-bookworm

# Install runtime system dependencies (util-linux for lscpu, libgomp1 for OpenMP)
RUN apt-get update && apt-get install -y --no-install-recommends \
    util-linux \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy migrations so they can be run in the distroless container
COPY --from=builder /app/alembic /app/alembic
COPY --from=builder /app/alembic.ini /app/alembic.ini

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/opt/venv/lib/python3.11/site-packages:/app"
ENV PYTHONUNBUFFERED=1
ENV APP_ENV=prod
ENV MODELS_DIR="/app/models"
ENV DATA_DIR="/app/data"
ENV UPLOAD_DIR="/app/data/uploads"

# Expose port
EXPOSE 8000

# Run the application via Uvicorn
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
