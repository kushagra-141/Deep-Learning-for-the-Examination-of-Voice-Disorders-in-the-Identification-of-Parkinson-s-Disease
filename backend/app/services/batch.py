"""P3-06: Batch CSV prediction runner.

Reads an uploaded CSV containing the 22 voice features (column names matching
the UCI dataset), runs every row through the ensemble, and writes a result
CSV with three appended columns:

    * `ensemble_probability` — soft-vote probability of Parkinson's
    * `ensemble_label`       — 0 / 1
    * `primary_model`        — name of the model used as the primary explainer

The job status is tracked in the `batch_jobs` table; the result CSV lives at
`Settings.UPLOAD_DIR / "batch" / "{job_id}.csv"`. Phase 4 swaps the in-process
BackgroundTasks runner for Celery without changing this contract.
"""
from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import ValidationError

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.ml.manager import ModelManager
from app.repositories.batch_job import update_batch_job
from app.schemas.feature import VoiceFeatures
from app.services.prediction_service import run_prediction

log = logging.getLogger(__name__)


def batch_dir() -> Path:
    """Return the directory where batch result CSVs live (created on demand)."""
    settings = get_settings()
    d = settings.UPLOAD_DIR / "batch"
    d.mkdir(parents=True, exist_ok=True)
    return d


def result_path(job_id: uuid.UUID) -> Path:
    return batch_dir() / f"{job_id}.csv"


def _predict_row(row: dict[str, Any], manager: ModelManager) -> dict[str, Any]:
    """Run a single CSV row through the ensemble. Raises ValidationError on bad input."""
    payload = {col: float(row[col]) for col in VoiceFeatures.FEATURE_ORDER}
    features = VoiceFeatures.model_validate(payload)
    response = run_prediction(features, manager, input_mode="batch")
    return {
        "ensemble_probability": response.ensemble.probability,
        "ensemble_label": response.ensemble.label,
        "primary_model": response.primary_model,
    }


async def run_batch_job(
    job_id: uuid.UUID,
    upload_path: Path,
    manager: ModelManager,
) -> None:
    """Process the uploaded CSV and write the result file.

    This runs in a `BackgroundTasks` context — it owns its own DB session
    because the request-scoped session is already closed by the time it fires.
    """
    settings = get_settings()
    out_path = result_path(job_id)

    async with AsyncSessionLocal() as db:
        try:
            await update_batch_job(
                db,
                job_id,
                status="running",
                processed=0,
            )

            df = pd.read_csv(upload_path)
            missing = [c for c in VoiceFeatures.FEATURE_ORDER if c not in df.columns]
            if missing:
                raise ValueError(f"Missing required columns: {missing}")

            if len(df) > settings.BATCH_MAX_ROWS:
                raise ValueError(
                    f"CSV has {len(df)} rows; max is {settings.BATCH_MAX_ROWS}"
                )

            results: list[dict[str, Any]] = []
            for _, row in df.iterrows():
                try:
                    results.append(_predict_row(row.to_dict(), manager))
                except ValidationError as exc:
                    results.append(
                        {
                            "ensemble_probability": float("nan"),
                            "ensemble_label": -1,
                            "primary_model": f"error: {exc.errors()[0]['msg']}",
                        }
                    )

            out = df.copy()
            for col in ("ensemble_probability", "ensemble_label", "primary_model"):
                out[col] = [r[col] for r in results]
            out.to_csv(out_path, index=False)

            await update_batch_job(
                db,
                job_id,
                status="succeeded",
                processed=len(df),
                row_count=len(df),
                result_path=str(out_path),
            )
            log.info("batch_job_succeeded", extra={"job_id": str(job_id), "rows": len(df)})
        except Exception as exc:
            log.exception("batch_job_failed", extra={"job_id": str(job_id)})
            await update_batch_job(
                db,
                job_id,
                status="failed",
                error_message=str(exc),
            )
        finally:
            try:
                upload_path.unlink(missing_ok=True)
            except OSError:
                pass
