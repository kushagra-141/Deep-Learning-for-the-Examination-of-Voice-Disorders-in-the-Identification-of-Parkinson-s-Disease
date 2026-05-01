# 02 — Backend Low-Level Design

> **Audience.** An engineer (or AI agent) implementing the FastAPI backend. Read `00_MASTER_PLAN.md` and `01_HLD.md` first.
>
> **Acceptance.** When this document's specs are realized, `make backend-test` passes with ≥ 80 % coverage and `curl http://localhost:8000/api/v1/healthz` returns `{"status":"ok"}`.

---

## 2.1 Module Layout

```
backend/
├── pyproject.toml                  # build + deps + tools (ruff, mypy, pytest)
├── uv.lock                         # or requirements.lock if not using uv
├── alembic.ini
├── README.md
├── Dockerfile                      # multi-stage; final = distroless
├── .dockerignore
├── data/
│   └── parkinsons.data             # bundled CSV (~38 KB)
├── models/                         # populated by training; mounted r/o in runtime
│   ├── manifest.json
│   ├── scaler.joblib
│   ├── pca.joblib                  # for PCA-RF only
│   ├── knn.joblib
│   ├── svm.joblib
│   ├── svm_calibrator.joblib
│   ├── decision_tree.joblib
│   ├── decision_tree_calibrator.joblib
│   ├── bagging.joblib
│   ├── lightgbm.joblib
│   ├── adaboost.joblib
│   ├── random_forest.joblib
│   ├── xgboost.joblib
│   └── pca_rf.joblib
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 20260501_0001_initial.py
├── scripts/
│   ├── train.py                    # CLI: trains all 9 models, writes manifest
│   ├── verify_models.py            # CLI: re-checks SHA-256 against manifest
│   └── seed_dataset.py             # CLI: ensures parkinsons.data exists
├── tests/
│   ├── conftest.py                 # shared fixtures: app, db, client
│   ├── unit/
│   │   ├── test_preprocessing.py
│   │   ├── test_feature_extractor.py
│   │   └── test_model_manager.py
│   ├── integration/
│   │   ├── test_predict_endpoint.py
│   │   ├── test_audio_endpoint.py
│   │   ├── test_batch_endpoint.py
│   │   ├── test_analytics_endpoint.py
│   │   └── test_auth.py
│   └── golden/                     # frozen reference outputs
│       ├── samples.jsonl
│       └── expected.jsonl
└── app/
    ├── __init__.py
    ├── main.py                     # FastAPI factory + lifespan
    ├── core/
    │   ├── __init__.py
    │   ├── config.py               # Settings (pydantic-settings)
    │   ├── logging.py              # structlog setup
    │   ├── observability.py        # Prometheus + Sentry + OTel wiring
    │   ├── security.py             # password hashing, JWT helpers
    │   ├── rate_limit.py           # slowapi limiter factory
    │   ├── errors.py               # AppException + global handlers
    │   └── deps.py                 # Depends() factories
    ├── db/
    │   ├── __init__.py
    │   ├── base.py                 # DeclarativeBase
    │   ├── session.py              # async engine + sessionmaker
    │   └── models/
    │       ├── __init__.py
    │       ├── prediction.py
    │       ├── batch_job.py
    │       ├── model_metadata.py
    │       ├── feedback.py
    │       └── audit_log.py
    ├── repositories/               # data access layer
    │   ├── __init__.py
    │   ├── prediction.py
    │   ├── batch_job.py
    │   ├── model_metadata.py
    │   └── feedback.py
    ├── schemas/                    # Pydantic v2 DTOs
    │   ├── __init__.py
    │   ├── feature.py              # VoiceFeatures, FeatureRanges
    │   ├── prediction.py           # PredictionRequest/Response, ModelPrediction
    │   ├── analytics.py            # DatasetStats, FeatureDistribution, ...
    │   ├── batch.py                # BatchJobRequest/Response/Status
    │   ├── model.py                # ModelInfo, ModelComparison
    │   ├── audio.py                # AudioPredictionResponse
    │   ├── feedback.py
    │   ├── auth.py                 # LoginRequest, TokenResponse
    │   └── errors.py               # ErrorPayload
    ├── services/                   # business logic (pure, framework-agnostic)
    │   ├── __init__.py
    │   ├── preprocessing.py        # load_dataset, get_train_test
    │   ├── training.py             # train_one(name) → fitted estimator
    │   ├── evaluation.py           # metrics + cross-val
    │   ├── feature_extraction.py   # parselmouth pipeline
    │   ├── prediction.py           # PredictionService (uses ModelManager)
    │   ├── explainability.py       # SHAP wrappers per model family
    │   ├── analytics.py            # dataset statistics
    │   └── batch.py                # batch job runner
    ├── ml/                         # model registry + manager
    │   ├── __init__.py
    │   ├── registry.py             # manifest read/write + integrity verify
    │   ├── manager.py              # ModelManager singleton
    │   └── ensemble.py             # voting ensemble
    ├── routers/                    # thin HTTP layer
    │   ├── __init__.py
    │   ├── predict.py
    │   ├── audio.py
    │   ├── batch.py
    │   ├── models.py
    │   ├── analytics.py
    │   ├── feedback.py
    │   ├── admin.py
    │   ├── auth.py
    │   └── health.py
    └── utils/
        ├── __init__.py
        ├── ids.py                  # UUID helpers, request-id
        ├── hashing.py              # SHA-256 helpers
        └── time.py
```

**Layering rule:** `routers` → `services` → `repositories` → `db.models`. A router never imports a `db.model` directly. A service never imports FastAPI types. The `ml/` package is allowed to be imported by services only.

---

## 2.2 Configuration (`app/core/config.py`)

```python
from functools import lru_cache
from pathlib import Path
from typing import Literal
from pydantic import Field, SecretStr, AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # --- App ---
    APP_NAME: str = "Parkinsons Voice Detection API"
    ENV: Literal["dev", "test", "prod"] = "dev"
    DEBUG: bool = False
    PUBLIC_BASE_URL: AnyHttpUrl = "http://localhost:5173"
    API_PREFIX: str = "/api/v1"

    # --- Paths ---
    PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]
    DATA_DIR: Path = PROJECT_ROOT / "data"
    MODELS_DIR: Path = PROJECT_ROOT / "models"
    UPLOAD_DIR: Path = PROJECT_ROOT / "data" / "uploads"

    # --- DB ---
    DATABASE_URL: str = "sqlite+aiosqlite:///./dev.db"
    DB_POOL_SIZE: int = 10
    DB_POOL_TIMEOUT_S: int = 30

    # --- Redis ---
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- Auth (admin only) ---
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD_HASH: SecretStr = SecretStr("")  # required in prod
    JWT_SECRET: SecretStr = SecretStr("change-me-in-prod")
    JWT_ALGO: str = "HS256"
    JWT_TTL_MIN: int = 60 * 12

    # --- Rate limits ---
    RL_PREDICT_PER_MIN: int = 60
    RL_AUDIO_PER_MIN: int = 10
    RL_BATCH_PER_MIN: int = 5

    # --- Audio ---
    AUDIO_MAX_BYTES: int = 5 * 1024 * 1024
    AUDIO_MAX_DURATION_S: float = 30.0
    AUDIO_TARGET_SR: int = 22_050

    # --- Batch ---
    BATCH_MAX_ROWS: int = 10_000
    BATCH_MAX_BYTES: int = 2 * 1024 * 1024

    # --- Observability ---
    SENTRY_DSN: SecretStr | None = None
    OTEL_EXPORTER_OTLP_ENDPOINT: str | None = None
    PROMETHEUS_ENABLED: bool = True
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    # --- Privacy ---
    HASH_DAILY_SALT: SecretStr = SecretStr("change-me")  # rotated nightly via cron

@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
```

`.env.example` (root):
```
ENV=prod
PUBLIC_BASE_URL=https://parkinsons.example.com
DATABASE_URL=postgresql+asyncpg://app:CHANGE_ME@postgres:5432/parkinsons
REDIS_URL=redis://redis:6379/0
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=$2b$12$...  # bcrypt
JWT_SECRET=...                  # 32+ random bytes (base64)
SENTRY_DSN=...
HASH_DAILY_SALT=...
```

---

## 2.3 Application Factory (`app/main.py`)

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.observability import init_observability, instrument_app
from app.core.errors import register_error_handlers
from app.core.rate_limit import limiter, rate_limit_handler
from app.ml.manager import ModelManager
from app.routers import predict, audio, batch, models, analytics, feedback, admin, auth, health

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings)
    init_observability(settings)
    app.state.model_manager = ModelManager.from_dir(settings.MODELS_DIR)
    app.state.model_manager.verify_integrity()
    yield
    # graceful shutdown hooks here

def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        docs_url=f"{settings.API_PREFIX}/docs",
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        lifespan=lifespan,
    )
    app.state.limiter = limiter
    app.add_exception_handler(*rate_limit_handler())
    register_error_handlers(app)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(settings.PUBLIC_BASE_URL)],
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )

    instrument_app(app)

    p = settings.API_PREFIX
    app.include_router(health.router, prefix=p, tags=["health"])
    app.include_router(predict.router, prefix=p, tags=["predict"])
    app.include_router(audio.router, prefix=p, tags=["audio"])
    app.include_router(batch.router, prefix=p, tags=["batch"])
    app.include_router(models.router, prefix=p, tags=["models"])
    app.include_router(analytics.router, prefix=p, tags=["analytics"])
    app.include_router(feedback.router, prefix=p, tags=["feedback"])
    app.include_router(auth.router, prefix=p, tags=["auth"])
    app.include_router(admin.router, prefix=p, tags=["admin"])
    return app

app = create_app()
```

---

## 2.4 Pydantic Schemas (`app/schemas/`)

### 2.4.1 Feature schema (`schemas/feature.py`)

22 fields with explicit `ge`/`le` ranges from dataset min/max ± 20 %, plus `examples`:

```python
from pydantic import BaseModel, Field, ConfigDict
from typing import ClassVar

class VoiceFeatures(BaseModel):
    """22 acoustic features in canonical column order."""
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    # Frequency
    mdvp_fo_hz: float = Field(alias="MDVP:Fo(Hz)", ge=50, le=300, examples=[154.23])
    mdvp_fhi_hz: float = Field(alias="MDVP:Fhi(Hz)", ge=50, le=600, examples=[197.10])
    mdvp_flo_hz: float = Field(alias="MDVP:Flo(Hz)", ge=50, le=300, examples=[116.32])
    # Jitter
    mdvp_jitter_pct: float = Field(alias="MDVP:Jitter(%)", ge=0, le=0.05, examples=[0.0067])
    mdvp_jitter_abs: float = Field(alias="MDVP:Jitter(Abs)", ge=0, le=0.001, examples=[0.00004])
    mdvp_rap: float = Field(alias="MDVP:RAP", ge=0, le=0.03, examples=[0.0034])
    mdvp_ppq: float = Field(alias="MDVP:PPQ", ge=0, le=0.04, examples=[0.0038])
    jitter_ddp: float = Field(alias="Jitter:DDP", ge=0, le=0.10, examples=[0.0102])
    # Shimmer
    mdvp_shimmer: float = Field(alias="MDVP:Shimmer", ge=0, le=0.20, examples=[0.029])
    mdvp_shimmer_db: float = Field(alias="MDVP:Shimmer(dB)", ge=0, le=2.0, examples=[0.282])
    shimmer_apq3: float = Field(alias="Shimmer:APQ3", ge=0, le=0.10, examples=[0.0145])
    shimmer_apq5: float = Field(alias="Shimmer:APQ5", ge=0, le=0.10, examples=[0.0179])
    mdvp_apq: float = Field(alias="MDVP:APQ", ge=0, le=0.15, examples=[0.024])
    shimmer_dda: float = Field(alias="Shimmer:DDA", ge=0, le=0.30, examples=[0.0436])
    # Harmonicity
    nhr: float = Field(alias="NHR", ge=0, le=1.0, examples=[0.0162])
    hnr: float = Field(alias="HNR", ge=5, le=40, examples=[22.4])
    # Nonlinear
    rpde: float = Field(alias="RPDE", ge=0, le=1, examples=[0.4985])
    dfa: float = Field(alias="DFA", ge=0, le=1, examples=[0.7180])
    spread1: float = Field(alias="spread1", ge=-10, le=0, examples=[-5.94])
    spread2: float = Field(alias="spread2", ge=0, le=1, examples=[0.226])
    d2: float = Field(alias="D2", ge=0, le=4, examples=[2.31])
    ppe: float = Field(alias="PPE", ge=0, le=1, examples=[0.207])

    FEATURE_ORDER: ClassVar[list[str]] = [
        "MDVP:Fo(Hz)", "MDVP:Fhi(Hz)", "MDVP:Flo(Hz)",
        "MDVP:Jitter(%)", "MDVP:Jitter(Abs)", "MDVP:RAP", "MDVP:PPQ", "Jitter:DDP",
        "MDVP:Shimmer", "MDVP:Shimmer(dB)", "Shimmer:APQ3", "Shimmer:APQ5",
        "MDVP:APQ", "Shimmer:DDA",
        "NHR", "HNR",
        "RPDE", "DFA", "spread1", "spread2", "D2", "PPE",
    ]

    def to_array(self) -> list[float]:
        d = self.model_dump(by_alias=True)
        return [d[k] for k in self.FEATURE_ORDER]
```

### 2.4.2 Prediction schemas (`schemas/prediction.py`)

```python
from pydantic import BaseModel, Field
from typing import Literal
from app.schemas.feature import VoiceFeatures

class PredictionRequest(BaseModel):
    features: VoiceFeatures
    model_name: Literal[
        "knn", "svm", "decision_tree", "bagging", "lightgbm",
        "adaboost", "random_forest", "xgboost", "pca_rf", "ensemble"
    ] | None = None  # None = run all + ensemble

class ShapContribution(BaseModel):
    feature: str
    value: float
    shap: float

class ModelPredictionOut(BaseModel):
    model_name: str
    model_version: str
    label: int = Field(ge=0, le=1)
    probability: float = Field(ge=0.0, le=1.0)
    shap_top: list[ShapContribution] | None = None  # top-5 by |shap|

class PredictionResponse(BaseModel):
    prediction_id: str
    created_at: str  # ISO8601 UTC
    input_mode: Literal["manual", "audio", "batch"]
    per_model: list[ModelPredictionOut]
    ensemble: ModelPredictionOut
    primary_model: str  # the model whose SHAP is highlighted
    disclaimer: str = (
        "Research/educational use only. Not a diagnostic device. "
        "Consult a qualified neurologist for medical advice."
    )
```

### 2.4.3 Other schemas (signatures only — full impl in §2.7)

- `schemas/audio.py`: `AudioPredictionResponse` extends `PredictionResponse` with `extracted_features: VoiceFeatures` and `audio_metadata: {duration_s, sample_rate, channels}`.
- `schemas/batch.py`: `BatchJobCreated{job_id, status_url}`, `BatchJobStatus{id, status, progress, row_count, error?}`.
- `schemas/model.py`: `ModelInfo{name, version, metrics, hyperparameters, trained_at}`, `ConfusionMatrix{tn, fp, fn, tp, labels}`.
- `schemas/analytics.py`: `DatasetStats{total, by_class}`, `FeatureDistribution{feature, bins[], counts[]}`, `CorrelationMatrix{features[], matrix[][]}`, `PCAProjection{components, explained_variance, points[{x,y,label}]}`.
- `schemas/feedback.py`: `FeedbackIn{prediction_id, rating, comment?}`.
- `schemas/auth.py`: `LoginIn{username, password}`, `TokenOut{access_token, expires_at}`.
- `schemas/errors.py`: `ErrorPayload{error: {code, message, request_id, details?}}`.

---

## 2.5 Database Layer

### 2.5.1 Engine + session (`app/db/session.py`)
```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import get_settings

_settings = get_settings()
engine = create_async_engine(
    _settings.DATABASE_URL,
    pool_size=_settings.DB_POOL_SIZE,
    pool_timeout=_settings.DB_POOL_TIMEOUT_S,
    future=True,
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

### 2.5.2 Base + tables (`app/db/models/`)
```python
# app/db/base.py
from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase): ...

# app/db/models/prediction.py
import uuid, datetime as dt
from sqlalchemy import String, ForeignKey, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class Prediction(Base):
    __tablename__ = "predictions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=lambda: dt.datetime.now(dt.UTC), index=True)
    features: Mapped[dict] = mapped_column(JSON, nullable=False)
    input_mode: Mapped[str] = mapped_column(String(16), nullable=False)
    batch_job_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("batch_jobs.id", ondelete="CASCADE"), nullable=True)
    client_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_consent: Mapped[str] = mapped_column(String(32), default="none")
    model_predictions: Mapped[list["ModelPrediction"]] = relationship(back_populates="prediction", cascade="all, delete-orphan")

class ModelPrediction(Base):
    __tablename__ = "model_predictions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("predictions.id", ondelete="CASCADE"), index=True)
    model_name: Mapped[str] = mapped_column(String(64), index=True)
    model_version: Mapped[str] = mapped_column(String(64))
    probability: Mapped[float]
    label: Mapped[int]
    shap_values: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    prediction: Mapped["Prediction"] = relationship(back_populates="model_predictions")
```

Other tables (`batch_jobs`, `model_metadata`, `feedback`, `audit_logs`) follow the same patterns. Schema in `01_HLD.md` §1.5.1.

> **Index policy**: any column in a `WHERE`/`ORDER BY` for an endpoint gets an index. Initial indexes: `predictions.created_at`, `model_predictions.prediction_id`, `model_predictions.model_name`, `batch_jobs.status`.

### 2.5.3 Alembic
- `alembic/env.py` reads `Settings().DATABASE_URL` and imports `Base.metadata`.
- Initial migration created with `alembic revision --autogenerate -m "initial"`.
- CI step: `alembic upgrade head` against ephemeral Postgres.

---

## 2.6 ML Pipeline

### 2.6.1 Preprocessing (`app/services/preprocessing.py`)
```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from app.schemas.feature import VoiceFeatures

def load_dataset(csv_path) -> pd.DataFrame:
    df = pd.read_csv(csv_path, sep=",", index_col="name")
    return df

def split_xy(df: pd.DataFrame):
    y = df["status"].values.astype(int)
    X = df[VoiceFeatures.FEATURE_ORDER].values.astype(float)
    return X, y

def train_test_split_xy(X, y, *, test_size=0.2, seed=1):
    return train_test_split(X, y, test_size=test_size, random_state=seed, stratify=y)

def fit_scaler(X_train) -> StandardScaler:
    """ONLY fit on training data — fixes the notebook's leakage bug."""
    sc = StandardScaler()
    sc.fit(X_train)
    return sc
```

### 2.6.2 Trainers (`app/services/training.py`)

One function per model. All accept `(X_train_scaled, y_train, *, seed=1)` and return a fitted estimator.

```python
def train_knn(X, y, *, seed=1):
    from sklearn.neighbors import KNeighborsClassifier
    return KNeighborsClassifier(n_neighbors=5).fit(X, y)

def train_svm(X, y, *, seed=1):
    from sklearn.svm import SVC
    return SVC(kernel="linear", probability=True, class_weight="balanced", random_state=seed).fit(X, y)

def train_decision_tree(X, y, *, seed=1):
    from sklearn.tree import DecisionTreeClassifier
    return DecisionTreeClassifier(max_depth=2, class_weight="balanced", random_state=seed).fit(X, y)

def train_bagging(X, y, *, seed=1):
    from sklearn.ensemble import BaggingClassifier
    from sklearn.tree import DecisionTreeClassifier
    base = DecisionTreeClassifier(max_depth=6, random_state=seed)
    return BaggingClassifier(estimator=base, n_estimators=300, n_jobs=-1, random_state=seed).fit(X, y)

def train_lightgbm(X, y, *, seed=1):
    from lightgbm import LGBMClassifier
    return LGBMClassifier(random_state=seed, class_weight="balanced", verbosity=-1).fit(X, y)

def train_adaboost(X, y, *, seed=1):
    from sklearn.ensemble import AdaBoostClassifier
    return AdaBoostClassifier(n_estimators=50, random_state=seed).fit(X, y)

def train_random_forest(X, y, *, seed=1):
    from sklearn.ensemble import RandomForestClassifier
    return RandomForestClassifier(n_estimators=30, criterion="entropy", class_weight="balanced", random_state=seed, n_jobs=-1).fit(X, y)

def train_xgboost(X, y, *, seed=1):
    from xgboost import XGBClassifier
    return XGBClassifier(random_state=seed, eval_metric="logloss", n_jobs=-1).fit(X, y)

def train_pca_rf(X, y, *, seed=1):
    from sklearn.decomposition import PCA
    from sklearn.ensemble import RandomForestClassifier
    pca = PCA(n_components=9, random_state=seed).fit(X)
    Xp = pca.transform(X)
    rf = RandomForestClassifier(n_estimators=30, criterion="entropy", class_weight="balanced", random_state=seed, n_jobs=-1).fit(Xp, y)
    return {"pca": pca, "rf": rf}
```

### 2.6.3 Calibration

For SVM/KNN/DT (and any model whose `predict_proba` is not well-calibrated), wrap with `CalibratedClassifierCV(method="isotonic", cv=5)` *fit on the training set only*. Store the calibrator alongside the base model.

### 2.6.4 Evaluation (`app/services/evaluation.py`)
```python
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                             roc_auc_score, confusion_matrix)
from sklearn.model_selection import cross_val_score, StratifiedKFold

def compute_metrics(estimator, X_test, y_test) -> dict:
    y_pred = estimator.predict(X_test)
    y_proba = estimator.predict_proba(X_test)[:, 1]
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    return dict(
        accuracy=accuracy_score(y_test, y_pred),
        precision=precision_score(y_test, y_pred),
        recall=recall_score(y_test, y_pred),
        f1=f1_score(y_test, y_pred),
        roc_auc=roc_auc_score(y_test, y_proba),
        confusion_matrix=dict(tn=int(tn), fp=int(fp), fn=int(fn), tp=int(tp)),
    )

def cv_score(estimator, X, y, *, k=5, seed=1) -> dict:
    cv = StratifiedKFold(n_splits=k, shuffle=True, random_state=seed)
    scores = cross_val_score(estimator, X, y, cv=cv, scoring="accuracy", n_jobs=-1)
    return dict(cv_accuracy_mean=float(scores.mean()), cv_accuracy_std=float(scores.std()))
```

### 2.6.5 Feature extraction from audio (`app/services/feature_extraction.py`)
```python
import numpy as np
import parselmouth
from parselmouth.praat import call
import librosa, soundfile as sf

def extract_features_from_audio(path: str, *, target_sr=22_050) -> dict:
    """Return the 22-feature dict using Praat via parselmouth.
    Only Fo / Fhi / Flo / Jitter / Shimmer / NHR / HNR are derived from Praat directly;
    RPDE / DFA / spread1 / spread2 / D2 / PPE require nonlinear-dynamics implementations."""
    y, sr = librosa.load(path, sr=target_sr, mono=True)
    snd = parselmouth.Sound(y, sr)
    pitch = snd.to_pitch(time_step=0.01, pitch_floor=75, pitch_ceiling=600)
    pp = call(snd, "To PointProcess (periodic, cc)", 75, 600)

    fo  = call(pitch, "Get mean", 0, 0, "Hertz")
    fhi = call(pitch, "Get maximum", 0, 0, "Hertz", "Parabolic")
    flo = call(pitch, "Get minimum", 0, 0, "Hertz", "Parabolic")

    jitter_local    = call(pp, "Get jitter (local)", 0, 0, 0.0001, 0.02, 1.3)
    jitter_local_abs= call(pp, "Get jitter (local, absolute)", 0, 0, 0.0001, 0.02, 1.3)
    rap             = call(pp, "Get jitter (rap)", 0, 0, 0.0001, 0.02, 1.3)
    ppq             = call(pp, "Get jitter (ppq5)", 0, 0, 0.0001, 0.02, 1.3)
    ddp             = call(pp, "Get jitter (ddp)", 0, 0, 0.0001, 0.02, 1.3)

    shimmer_local    = call([snd, pp], "Get shimmer (local)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
    shimmer_local_db = call([snd, pp], "Get shimmer (local_dB)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
    apq3             = call([snd, pp], "Get shimmer (apq3)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
    apq5             = call([snd, pp], "Get shimmer (apq5)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
    apq              = call([snd, pp], "Get shimmer (apq11)", 0, 0, 0.0001, 0.02, 1.3, 1.6)
    dda              = call([snd, pp], "Get shimmer (dda)", 0, 0, 0.0001, 0.02, 1.3, 1.6)

    harmonicity = snd.to_harmonicity_cc()
    hnr = call(harmonicity, "Get mean", 0, 0)
    nhr = 1 / (10 ** (hnr / 10) + 1e-9)  # approximate

    # Nonlinear features — use the open-source `nolds` / `pyrpde` / custom implementations
    from app.services.nonlinear import rpde, dfa, spread1, spread2, d2, ppe
    nl = dict(
        RPDE=rpde(y, sr), DFA=dfa(y), spread1=spread1(pitch),
        spread2=spread2(pitch), D2=d2(y), PPE=ppe(pitch),
    )

    return {
        "MDVP:Fo(Hz)": fo, "MDVP:Fhi(Hz)": fhi, "MDVP:Flo(Hz)": flo,
        "MDVP:Jitter(%)": jitter_local, "MDVP:Jitter(Abs)": jitter_local_abs,
        "MDVP:RAP": rap, "MDVP:PPQ": ppq, "Jitter:DDP": ddp,
        "MDVP:Shimmer": shimmer_local, "MDVP:Shimmer(dB)": shimmer_local_db,
        "Shimmer:APQ3": apq3, "Shimmer:APQ5": apq5,
        "MDVP:APQ": apq, "Shimmer:DDA": dda,
        "NHR": nhr, "HNR": hnr,
        **nl,
    }
```

> [!NOTE]
> The nonlinear features (RPDE, DFA, spread1/2, D2, PPE) are not available out-of-the-box in `parselmouth`. Implement them in `app/services/nonlinear.py` using `nolds` for DFA / D2, and port the Little (2008) RPDE/PPE algorithms (see referenced research papers). If implementation slips, the audio endpoint may temporarily fall back to inferring those values from the closest dataset sample (clearly labeled as "estimated"). This is captured as **risk R-04** in the master plan.

### 2.6.6 Model registry (`app/ml/registry.py`)
```python
import hashlib, json, joblib
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class ModelEntry:
    name: str
    version: str
    path: str
    calibrator_path: str | None
    sha256: str
    metrics: dict
    hyperparameters: dict
    trained_at: str

def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def write_manifest(models_dir: Path, scaler_meta: dict, entries: list[ModelEntry]) -> None:
    manifest = {
        "schema_version": 1,
        "scaler": scaler_meta,
        "models": [asdict(e) for e in entries],
    }
    (models_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

def load_manifest(models_dir: Path) -> dict:
    return json.loads((models_dir / "manifest.json").read_text())

def verify_integrity(models_dir: Path) -> None:
    m = load_manifest(models_dir)
    for entry in [m["scaler"], *m["models"]]:
        if sha256_of(models_dir / entry["path"]) != entry["sha256"]:
            raise RuntimeError(f"Integrity check failed for {entry['path']}")
```

### 2.6.7 Model manager (`app/ml/manager.py`)
```python
import joblib
import numpy as np
from pathlib import Path
from app.ml.registry import load_manifest, verify_integrity

class ModelManager:
    def __init__(self, scaler, models: dict, calibrators: dict, manifest: dict, pca):
        self.scaler = scaler; self.models = models; self.calibrators = calibrators
        self.manifest = manifest; self.pca = pca

    @classmethod
    def from_dir(cls, models_dir: Path) -> "ModelManager":
        m = load_manifest(models_dir)
        scaler = joblib.load(models_dir / m["scaler"]["path"])
        pca = joblib.load(models_dir / "pca.joblib") if (models_dir / "pca.joblib").exists() else None
        models, calibrators = {}, {}
        for entry in m["models"]:
            models[entry["name"]] = joblib.load(models_dir / entry["path"])
            if entry.get("calibrator_path"):
                calibrators[entry["name"]] = joblib.load(models_dir / entry["calibrator_path"])
        return cls(scaler, models, calibrators, m, pca)

    def verify_integrity(self) -> None:
        verify_integrity(Path(self.manifest["__path__"]))  # pass dir via env

    def predict_proba(self, name: str, x: np.ndarray) -> float:
        x_scaled = self.scaler.transform(x.reshape(1, -1))
        if name == "pca_rf":
            x_scaled = self.pca.transform(x_scaled)
        model = self.models[name]
        if name in self.calibrators:
            return float(self.calibrators[name].predict_proba(x_scaled)[0, 1])
        return float(model.predict_proba(x_scaled)[0, 1])
```

### 2.6.8 Ensemble (`app/ml/ensemble.py`)

Soft-voting of the top-3 by CV accuracy. Mean of calibrated probabilities. Returns name `"ensemble"`, version derived from the union of contributing model versions, label = `int(p ≥ 0.5)`.

### 2.6.9 Explainability (`app/services/explainability.py`)
```python
import shap
from functools import lru_cache

@lru_cache(maxsize=16)
def explainer_for(model_name: str, mm):
    model = mm.models[model_name]
    family = type(model).__name__
    if family in {"LGBMClassifier", "XGBClassifier", "RandomForestClassifier",
                  "DecisionTreeClassifier", "BaggingClassifier", "AdaBoostClassifier"}:
        return shap.TreeExplainer(model)
    # SVM/KNN/PCA-RF: use KernelExplainer with a small background sample
    background = mm.scaler.transform(mm.training_background)  # cached on disk
    return shap.KernelExplainer(model.predict_proba, background, nsamples=64)

def shap_top_k(mm, model_name: str, x_scaled, *, k=5, feature_names):
    expl = explainer_for(model_name, mm)
    sv = expl.shap_values(x_scaled)
    sv1 = sv[1] if isinstance(sv, list) else sv  # class=1
    pairs = sorted(
        zip(feature_names, x_scaled.ravel().tolist(), sv1.ravel().tolist()),
        key=lambda t: abs(t[2]), reverse=True,
    )[:k]
    return [{"feature": f, "value": v, "shap": s} for f, v, s in pairs]
```

---

## 2.7 Endpoints

> All endpoints are under `/api/v1`. All success responses include `X-Request-ID`. All errors follow `ErrorPayload`. Pagination is cursor-based when used.

### 2.7.1 Health

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/healthz` | none | Liveness; always 200 if process up. |
| GET | `/readyz` | none | Readiness; checks DB ping and `app.state.model_manager`. 200 / 503. |

### 2.7.2 Predict

`POST /predict`

**Request** (`application/json`):
```json
{
  "features": { "MDVP:Fo(Hz)": 154.23, "MDVP:Fhi(Hz)": 197.10, "...": "..." },
  "model_name": null
}
```

**Response 200**:
```json
{
  "prediction_id": "f3a2…",
  "created_at": "2026-04-30T18:42:11Z",
  "input_mode": "manual",
  "primary_model": "lightgbm",
  "per_model": [
    {"model_name": "knn", "model_version": "2026.04.30+1", "label": 1, "probability": 0.83, "shap_top": null},
    "..."
  ],
  "ensemble": {"model_name": "ensemble", "model_version": "...", "label": 1, "probability": 0.91, "shap_top": [{"feature": "PPE", "value": 0.31, "shap": 0.12}, "..."]},
  "disclaimer": "Research/educational use only. Not a diagnostic device. ..."
}
```

**Errors**: `422` for validation, `429` for rate-limit, `503` if models not loaded.

`GET /predict/sample?label=0|1|random`

Returns a randomly chosen row from the dataset already shaped as `VoiceFeatures`.

### 2.7.3 Audio

`POST /audio/predict` (`multipart/form-data`, field `file`, optional `model_name`)

**Validation**: size, mime, duration, mono/stereo (downmix). On success returns `AudioPredictionResponse`. **Audio bytes are not persisted** unless `Consent-Store-Audio: true` header is supplied.

### 2.7.4 Batch

| Method | Path | Description |
|---|---|---|
| `POST` | `/batch` | Multipart CSV upload. Returns `202 {job_id, status_url}`. |
| `GET`  | `/batch/{job_id}` | Status: `queued`/`running`/`succeeded`/`failed`, progress % . |
| `GET`  | `/batch/{job_id}/download` | Streams CSV with appended `prediction`, `probability`, `model_used` columns. |
| `DELETE` | `/batch/{job_id}` | Admin only; deletes job + uploaded file + results. |

Job runner uses `BackgroundTasks`. Phase 4 swaps to Celery without changing the API contract.

### 2.7.5 Models

| Method | Path | Description |
|---|---|---|
| `GET` | `/models` | Lists all 9 + ensemble: name, version, metrics, hyperparameters, training timestamp. |
| `GET` | `/models/{name}/confusion-matrix` | Pre-computed at training time; loaded from `metrics`. |
| `GET` | `/models/{name}/roc` | Returns FPR/TPR arrays. |
| `GET` | `/models/{name}/pr` | Precision/recall arrays. |
| `GET` | `/models/{name}/calibration` | Reliability diagram bins. |
| `GET` | `/models/compare` | Side-by-side metric table. |

### 2.7.6 Analytics

| Method | Path | Description |
|---|---|---|
| `GET` | `/analytics/dataset-stats` | Total, by-class counts, % balance. |
| `GET` | `/analytics/feature/{name}` | Histogram + KDE points + per-class boxplot. |
| `GET` | `/analytics/correlation` | 22×22 matrix. Cached (Redis 1 h). |
| `GET` | `/analytics/pca` | 2-D + 3-D PCA scatter, points labeled by class. |

### 2.7.7 Feedback

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/feedback` | none, but requires valid `prediction_id` | 1–5 stars + optional comment. Rate-limited 5/min/IP. |

### 2.7.8 Auth + Admin

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/login` | none | `{username, password}` → sets HttpOnly `Authorization` cookie + JSON token. |
| `POST` | `/auth/logout` | cookie | Clears cookie. |
| `GET`  | `/admin/predictions?cursor=&limit=50` | admin | Paginated history. |
| `GET`  | `/admin/feedback?cursor=&limit=50` | admin | Reviews feedback. |
| `GET`  | `/admin/audit-log?cursor=&limit=100` | admin | Recent admin actions. |
| `POST` | `/admin/retrain` | admin | Triggers training inside the runtime container (Phase 4+; behind feature flag). |

---

## 2.8 Error Handling (`app/core/errors.py`)

```python
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

class AppException(Exception):
    code: str = "app_error"
    http_status: int = 500
    message: str = "Internal error"
    def __init__(self, message: str | None = None, **details):
        self.details = details
        if message: self.message = message

class NotFound(AppException):       code, http_status = "not_found", 404
class ValidationFailed(AppException): code, http_status = "validation_failed", 422
class RateLimited(AppException):    code, http_status = "rate_limited", 429
class IntegrityFailure(AppException):code, http_status = "model_integrity_failure", 503
class ModelUnavailable(AppException):code, http_status = "model_unavailable", 503

def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def _h(req: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.http_status,
            content={"error": {"code": exc.code, "message": exc.message,
                               "request_id": req.state.request_id, "details": exc.details}},
        )
    @app.exception_handler(RequestValidationError)
    async def _v(req: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"error": {"code": "validation_failed",
                               "message": "Invalid request body",
                               "request_id": req.state.request_id,
                               "details": exc.errors()}},
        )
```

---

## 2.9 Middleware & Dependencies

- **Request-ID middleware** (custom): reads `X-Request-ID` header or generates UUID4; sets `request.state.request_id`; echoes back; injects into structlog context via `contextvars`.
- **Body-size limit** middleware: rejects > `Settings.AUDIO_MAX_BYTES` for `/audio/*` and > `Settings.BATCH_MAX_BYTES` for `/batch`.
- **Rate-limit dep**: per-route `Depends(limiter.limit("60/minute"))`.
- **Auth dep**: `Depends(get_current_admin)` reads JWT cookie, validates signature + expiry, returns `AdminUser` or raises 401.

---

## 2.10 Logging (`app/core/logging.py`)

```python
import structlog, logging, sys
def configure_logging(settings):
    logging.basicConfig(level=settings.LOG_LEVEL, format="%(message)s", stream=sys.stdout)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, settings.LOG_LEVEL)),
        cache_logger_on_first_use=True,
    )
```

Every request gets a log line with `request_id`, `method`, `path`, `status`, `duration_ms`, `user_id` (admin), `client_fp`.

---

## 2.11 Observability (`app/core/observability.py`)

```python
import sentry_sdk
from prometheus_fastapi_instrumentator import Instrumentator
from sentry_sdk.integrations.fastapi import FastApiIntegration

def init_observability(settings):
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN.get_secret_value(),
            integrations=[FastApiIntegration()],
            traces_sample_rate=0.1,
            send_default_pii=False,
            environment=settings.ENV,
        )

def instrument_app(app):
    Instrumentator(should_group_status_codes=True, should_ignore_untemplated=True
        ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
```

**Custom metrics** (`app/services/prediction.py`):
```python
from prometheus_client import Counter, Histogram
PRED_TOTAL = Counter("predictions_total", "Predictions made", ["model", "label"])
AUDIO_LATENCY = Histogram("audio_extraction_seconds", "Audio feature extraction latency")
BATCH_TOTAL = Counter("batch_jobs_total", "Batch jobs processed", ["status"])
```

---

## 2.12 Security Specifics

- **Password hashing**: `passlib[bcrypt]` with rounds=12.
- **JWT**: HS256 with `Settings.JWT_SECRET`; `iat`, `exp`, `sub`, `role=admin` claims; `httponly=True`, `secure=True`, `samesite="strict"` cookie.
- **CORS**: locked to `PUBLIC_BASE_URL`.
- **Headers** (set by Caddy, but assert in tests):
  ```
  Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: microphone=(self), camera=(), geolocation=()
  Content-Security-Policy: default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self' https://o0.ingest.sentry.io
  ```
- **Body sizes**: enforced server-side and Caddy-side.
- **Pickle**: only `joblib.load` from `MODELS_DIR`; verify SHA-256 from `manifest.json` at startup; manifest itself HMAC-signed in prod (`MANIFEST_HMAC_KEY`).
- **No stack traces leak**: `Settings.DEBUG` only `True` in dev; production handler returns `"Internal error"` + `request_id`.

---

## 2.13 Testing

- **Unit** (`tests/unit/`): every service has at least one unit test covering happy + edge.
- **Integration** (`tests/integration/`): use `httpx.AsyncClient(app=app)` against a test app with SQLite (`sqlite+aiosqlite:///:memory:`) and an in-memory `fakeredis` instance.
- **Golden samples**: `tests/golden/samples.jsonl` has 10 known feature vectors; `expected.jsonl` has the per-model probabilities to ±1e-4 tolerance. Any change in models requires regeneration with a documented reason.
- **Coverage**: `pytest --cov=app --cov-fail-under=80`. Phase 4 raises to 90.
- **Audio tests**: ship 3 short WAVs in `tests/fixtures/audio/` (1 s sine 220 Hz, 1 s silence, 3 s synthesized voice). Assert no exceptions and feature vector shape == 22.
- **Mutation tests** (Phase 4+): `mutmut` against `services/`.

---

## 2.14 Performance & Limits

- Models loaded once at startup → kept warm → predict is microseconds for tree models, ms for SVM.
- `/analytics/correlation` cached in Redis for 1 h (it's deterministic on bundled data).
- DB connections via async pool (10 conns).
- Background batch jobs hold a semaphore of 2 concurrent jobs to avoid CPU thrash.
- Uvicorn started with `--workers 2 --proxy-headers --forwarded-allow-ips '*'` behind Caddy.

---

## 2.15 Required CLI Scripts

```
backend/scripts/train.py         # python -m scripts.train --seed 1 --out models/
backend/scripts/verify_models.py # exits 1 if any sha256 mismatches
backend/scripts/seed_dataset.py  # downloads parkinsons.data if missing (curl + sha)
```

Each script has a `if __name__ == "__main__":` and uses `argparse`, exit codes, and `structlog`.

---

## 2.16 Definition of Done for the Backend

- `make backend-test` is green, coverage ≥ 80 %.
- `make backend-lint` (Ruff + mypy strict) green.
- `python -m scripts.train` produces a `manifest.json` with all 9 models present and their CV accuracy ≥ 80 %.
- `make backend-run` boots in < 5 s and `/api/v1/readyz` returns 200.
- All endpoints in §2.7 have at least one integration test.
- A new ADR is added if any choice in this LLD is overridden.
