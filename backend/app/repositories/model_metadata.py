"""P1-13: Model metadata repository.

While models are stored on disk in the models/ directory with a manifest.json,
we might also want to track them in the DB for analytics and history.
For the MVP, the manifest.json is the source of truth, so this is a stub
ready for future expansion if DB syncing is required.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession


async def sync_models_to_db(db: AsyncSession, manifest: dict) -> None:
    """Stub: sync manifest contents to a DB table if needed in the future."""
    pass
