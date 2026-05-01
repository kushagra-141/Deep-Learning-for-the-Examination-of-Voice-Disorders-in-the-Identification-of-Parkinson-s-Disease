"""P3-06: Batch CSV prediction endpoints."""
from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

import structlog
from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import FileResponse

from app.core.config import get_settings
from app.core.deps import SessionDep
from app.core.rate_limit import limiter
from app.repositories.batch_job import create_batch_job, get_batch_job
from app.schemas.batch import BatchJobCreated, BatchJobStatus
from app.services.batch import result_path, run_batch_job

router = APIRouter()
log = structlog.get_logger(__name__)
_settings = get_settings()

ALLOWED_MIME_TYPES = {"text/csv", "application/vnd.ms-excel", "application/csv"}


@router.post("/", response_model=BatchJobCreated, status_code=202)
@limiter.limit(f"{_settings.RL_BATCH_PER_MIN}/minute")
async def create_batch(
    request: Request,
    db: SessionDep,
    background: BackgroundTasks,
    file: UploadFile = File(...),
) -> BatchJobCreated:
    """Accept a CSV upload and queue a batch prediction job."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # MIME check is best-effort — many clients submit text/csv as application/octet-stream.
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES and not (
        file.content_type.startswith("text/") or file.filename.lower().endswith(".csv")
    ):
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported media type: {file.content_type}. CSV expected.",
        )

    settings = get_settings()
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    fd, tmp_path_str = tempfile.mkstemp(suffix=".csv", dir=str(settings.UPLOAD_DIR))
    tmp_path = Path(tmp_path_str)

    try:
        bytes_read = 0
        chunk_size = 1024 * 1024
        with open(fd, "wb") as buffer:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                bytes_read += len(chunk)
                if bytes_read > settings.BATCH_MAX_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=(
                            f"CSV exceeds maximum allowed size of "
                            f"{settings.BATCH_MAX_BYTES // 1024} KB"
                        ),
                    )
                buffer.write(chunk)
        if bytes_read == 0:
            raise HTTPException(status_code=400, detail="Uploaded CSV is empty")
    except HTTPException:
        tmp_path.unlink(missing_ok=True)
        raise
    except Exception as exc:
        tmp_path.unlink(missing_ok=True)
        log.error("batch_upload_failed", error=str(exc))
        raise HTTPException(status_code=500, detail="Upload failed") from None

    job = await create_batch_job(db, row_count=0)
    # `status` defaults to "pending" in the ORM; flip to LLD vocabulary before returning.
    job.status = "queued"
    await db.commit()

    manager = request.app.state.model_manager
    background.add_task(run_batch_job, job.id, tmp_path, manager)

    return BatchJobCreated(
        job_id=str(job.id),
        status_url=f"{settings.API_PREFIX}/batch/{job.id}",
    )


@router.get("/{job_id}", response_model=BatchJobStatus)
async def get_status(job_id: str, db: SessionDep) -> BatchJobStatus:
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Unknown job_id") from None

    job = await get_batch_job(db, job_uuid)
    if job is None:
        raise HTTPException(status_code=404, detail="Unknown job_id")

    progress = (
        float(job.processed) / float(job.row_count) if job.row_count > 0 else 0.0
    )
    # Coerce ORM strings to the LLD-vocabulary literal accepted by the schema.
    status_map = {"pending": "queued", "done": "succeeded"}
    status_value = status_map.get(job.status, job.status)
    if status_value not in ("queued", "running", "succeeded", "failed"):
        status_value = "queued"

    return BatchJobStatus(
        id=str(job.id),
        status=status_value,  # type: ignore[arg-type]
        progress=min(1.0, max(0.0, progress)),
        row_count=job.row_count,
        error=job.error_message,
    )


@router.get("/{job_id}/download")
async def download_result(job_id: str, db: SessionDep) -> FileResponse:
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Unknown job_id") from None

    job = await get_batch_job(db, job_uuid)
    if job is None:
        raise HTTPException(status_code=404, detail="Unknown job_id")
    if job.status not in ("done", "succeeded"):
        raise HTTPException(status_code=409, detail=f"Job not ready (status={job.status})")

    path = result_path(job_uuid)
    if not path.exists():
        raise HTTPException(status_code=410, detail="Result file no longer available")
    return FileResponse(
        path=path,
        media_type="text/csv",
        filename=f"batch_predictions_{job_id}.csv",
    )
