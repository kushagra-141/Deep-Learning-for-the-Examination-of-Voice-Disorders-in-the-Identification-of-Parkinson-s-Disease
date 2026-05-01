"""Prediction + ModelPrediction ORM models."""
from __future__ import annotations

import datetime as dt
import uuid

from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: dt.datetime.now(dt.timezone.utc),
        index=True,
    )
    features: Mapped[dict] = mapped_column(JSON, nullable=False)
    input_mode: Mapped[str] = mapped_column(String(16), nullable=False)
    batch_job_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("batch_jobs.id", ondelete="CASCADE"), nullable=True
    )
    client_fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_consent: Mapped[str] = mapped_column(String(32), default="none")

    model_predictions: Mapped[list["ModelPrediction"]] = relationship(
        back_populates="prediction", cascade="all, delete-orphan"
    )


class ModelPrediction(Base):
    __tablename__ = "model_predictions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    prediction_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("predictions.id", ondelete="CASCADE"), index=True
    )
    model_name: Mapped[str] = mapped_column(String(64), index=True)
    model_version: Mapped[str] = mapped_column(String(64))
    probability: Mapped[float]
    label: Mapped[int]
    shap_values: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    prediction: Mapped["Prediction"] = relationship(back_populates="model_predictions")
