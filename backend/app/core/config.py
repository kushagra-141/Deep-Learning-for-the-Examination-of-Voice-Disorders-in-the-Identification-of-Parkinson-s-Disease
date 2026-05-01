"""P1-02: Application settings via pydantic-settings.

All configuration is read from environment variables / .env file.
Use `get_settings()` everywhere — it is cached after first call.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import AnyHttpUrl, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── App ───────────────────────────────────────────────────────────────────
    APP_NAME: str = "Parkinson's Voice Detection API"
    ENV: Literal["dev", "test", "prod"] = "dev"
    DEBUG: bool = False
    PUBLIC_BASE_URL: str = "http://localhost:5173"
    API_PREFIX: str = "/api/v1"

    # ── Paths ─────────────────────────────────────────────────────────────────
    PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
    DATA_DIR: Path = Path(__file__).resolve().parents[2] / "data"
    MODELS_DIR: Path = Path(__file__).resolve().parents[2] / "models"
    UPLOAD_DIR: Path = Path(__file__).resolve().parents[2] / "data" / "uploads"

    # ── DB ────────────────────────────────────────────────────────────────────
    DATABASE_URL: str = "sqlite+aiosqlite:///./dev.db"
    DB_POOL_SIZE: int = 10
    DB_POOL_TIMEOUT_S: int = 30

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── Auth (admin only) ─────────────────────────────────────────────────────
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD_HASH: SecretStr = SecretStr("")  # required in prod
    JWT_SECRET: SecretStr = SecretStr("change-me-in-prod-32-bytes-minimum")
    JWT_ALGO: str = "HS256"
    JWT_TTL_MIN: int = 60 * 12  # 12 hours

    # ── Rate limits ───────────────────────────────────────────────────────────
    RL_PREDICT_PER_MIN: int = 60
    RL_AUDIO_PER_MIN: int = 10
    RL_BATCH_PER_MIN: int = 5

    # ── Audio ─────────────────────────────────────────────────────────────────
    AUDIO_MAX_BYTES: int = 5 * 1024 * 1024  # 5 MB
    AUDIO_MAX_DURATION_S: float = 30.0
    AUDIO_TARGET_SR: int = 22_050

    # ── Batch ─────────────────────────────────────────────────────────────────
    BATCH_MAX_ROWS: int = 10_000
    BATCH_MAX_BYTES: int = 2 * 1024 * 1024  # 2 MB

    # ── Observability ─────────────────────────────────────────────────────────
    SENTRY_DSN: SecretStr | None = None
    PROMETHEUS_ENABLED: bool = True
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # ── Privacy ───────────────────────────────────────────────────────────────
    HASH_DAILY_SALT: SecretStr = SecretStr("change-me")  # rotated nightly via cron

    # ── LLM ───────────────────────────────────────────────────────────────────
    GROQ_API_KEY: SecretStr | None = None
    GEMINI_API_KEY: SecretStr | None = None
    OPENROUTER_API_KEY: SecretStr | None = None
    LLM_PRIMARY_PROVIDER: str = "groq"
    LLM_FALLBACK_PROVIDER: str = "gemini"
    LLM_TIMEOUT_S: int = 30
    LLM_DAILY_TOKEN_BUDGET: int = 500_000


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
