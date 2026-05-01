"""P1-13: Feedback repository."""
from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.feedback import Feedback


async def create_feedback(
    db: AsyncSession, prediction_id: uuid.UUID, rating: int, comment: str | None = None
) -> Feedback:
    feedback = Feedback(prediction_id=prediction_id, rating=rating, comment=comment)
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    return feedback


async def get_feedback_for_prediction(db: AsyncSession, prediction_id: uuid.UUID) -> list[Feedback]:
    stmt = select(Feedback).where(Feedback.prediction_id == prediction_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())
