"""initial

Revision ID: 20260501_0001
Revises:
Create Date: 2026-05-01 08:00:00+00:00

Creates all five tables in dependency order: batch_jobs, predictions,
model_predictions, feedback, audit_logs. UUID columns use SQLAlchemy's
cross-platform `Uuid` type (CHAR(32) on SQLite, native UUID on PostgreSQL).
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260501_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "batch_jobs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="pending"),
        sa.Column("row_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("result_path", sa.Text(), nullable=True),
        sa.Column("client_fingerprint", sa.String(length=64), nullable=True),
    )
    op.create_index("ix_batch_jobs_created_at", "batch_jobs", ["created_at"])
    op.create_index("ix_batch_jobs_status", "batch_jobs", ["status"])

    op.create_table(
        "predictions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("features", sa.JSON(), nullable=False),
        sa.Column("input_mode", sa.String(length=16), nullable=False),
        sa.Column(
            "batch_job_id",
            sa.Uuid(),
            sa.ForeignKey("batch_jobs.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("client_fingerprint", sa.String(length=64), nullable=True),
        sa.Column("user_consent", sa.String(length=32), nullable=False, server_default="none"),
    )
    op.create_index("ix_predictions_created_at", "predictions", ["created_at"])

    op.create_table(
        "model_predictions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "prediction_id",
            sa.Uuid(),
            sa.ForeignKey("predictions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("model_name", sa.String(length=64), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("probability", sa.Float(), nullable=False),
        sa.Column("label", sa.Integer(), nullable=False),
        sa.Column("shap_values", sa.JSON(), nullable=True),
    )
    op.create_index("ix_model_predictions_prediction_id", "model_predictions", ["prediction_id"])
    op.create_index("ix_model_predictions_model_name", "model_predictions", ["model_name"])

    op.create_table(
        "feedback",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "prediction_id",
            sa.Uuid(),
            sa.ForeignKey("predictions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
    )
    op.create_index("ix_feedback_prediction_id", "feedback", ["prediction_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("actor", sa.String(length=64), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("resource", sa.String(length=128), nullable=True),
        sa.Column("detail", sa.JSON(), nullable=True),
    )
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_index("ix_audit_logs_actor", "audit_logs", ["actor"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])


def downgrade() -> None:
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index("ix_audit_logs_actor", table_name="audit_logs")
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("ix_feedback_prediction_id", table_name="feedback")
    op.drop_table("feedback")

    op.drop_index("ix_model_predictions_model_name", table_name="model_predictions")
    op.drop_index("ix_model_predictions_prediction_id", table_name="model_predictions")
    op.drop_table("model_predictions")

    op.drop_index("ix_predictions_created_at", table_name="predictions")
    op.drop_table("predictions")

    op.drop_index("ix_batch_jobs_status", table_name="batch_jobs")
    op.drop_index("ix_batch_jobs_created_at", table_name="batch_jobs")
    op.drop_table("batch_jobs")
