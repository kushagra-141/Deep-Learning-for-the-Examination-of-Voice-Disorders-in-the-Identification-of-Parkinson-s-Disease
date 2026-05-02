"""add narrative columns to predictions (P3.5-10)

Revision ID: 20260518_0010
Revises: 20260501_0001
Create Date: 2026-05-18 12:00:00+00:00
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260518_0010"
down_revision = "20260501_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "predictions",
        sa.Column("narrative", sa.Text(), nullable=True),
    )
    op.add_column(
        "predictions",
        sa.Column("narrative_model", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "predictions",
        sa.Column(
            "narrative_generated_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("predictions", "narrative_generated_at")
    op.drop_column("predictions", "narrative_model")
    op.drop_column("predictions", "narrative")
