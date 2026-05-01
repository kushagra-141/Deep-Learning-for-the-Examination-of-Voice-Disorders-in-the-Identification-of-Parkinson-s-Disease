"""P1-13: Batch job repository."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.batch_job import BatchJob


async def create_batch_job(db: AsyncSession, row_count: int, fingerprint: str | None = None) -> BatchJob:
    job = BatchJob(row_count=row_count, client_fingerprint=fingerprint)
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


async def get_batch_job(db: AsyncSession, job_id: uuid.UUID) -> BatchJob | None:
    stmt = select(BatchJob).where(BatchJob.id == job_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def update_batch_job(
    db: AsyncSession, 
    job_id: uuid.UUID, 
    **kwargs
) -> BatchJob | None:
    job = await get_batch_job(db, job_id)
    if job:
        for k, v in kwargs.items():
            setattr(job, k, v)
        await db.commit()
        await db.refresh(job)
    return job
