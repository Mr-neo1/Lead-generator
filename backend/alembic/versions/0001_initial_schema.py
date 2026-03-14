"""Initial schema - baseline for all current tables.

This migration represents the full schema that was previously managed
by the hand-rolled migrate.py script. Going forward, use Alembic exclusively:

  # Generate a new migration after changing models.py:
  cd backend
  alembic revision --autogenerate -m "describe your change"

  # Apply pending migrations:
  alembic upgrade head

  # Roll back one step:
  alembic downgrade -1

Revision ID: 0001
Revises:
Create Date: 2026-03-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── scraping_jobs ────────────────────────────────────────────────────────
    op.create_table(
        "scraping_jobs",
        sa.Column("job_id", sa.String(), primary_key=True, index=True),
        sa.Column("keyword", sa.String(), index=True),
        sa.Column("location", sa.String(), index=True),
        sa.Column("radius", sa.Integer()),
        sa.Column("grid_size", sa.String()),
        sa.Column("status", sa.String(), default="pending", index=True),
        sa.Column("total_tasks", sa.Integer(), default=0),
        sa.Column("completed_tasks", sa.Integer(), default=0),
        sa.Column("failed_tasks", sa.Integer(), default=0),
        sa.Column("leads_found", sa.Integer(), default=0),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # ── businesses ───────────────────────────────────────────────────────────
    op.create_table(
        "businesses",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("place_id", sa.String(), unique=True, index=True),
        sa.Column(
            "source_job_id",
            sa.String(),
            sa.ForeignKey("scraping_jobs.job_id"),
            nullable=True,
            index=True,
        ),
        sa.Column("name", sa.String(), index=True),
        sa.Column("phone", sa.String(), nullable=True, index=True),
        sa.Column("website", sa.String(), nullable=True),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("reviews", sa.Integer(), nullable=True),
        sa.Column("category", sa.String(), nullable=True, index=True),
        sa.Column("address", sa.String(), nullable=True),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lng", sa.Float(), nullable=True),
        sa.Column("maps_url", sa.String()),
        sa.Column("tags", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), default="new", index=True),
        sa.Column("is_blacklisted", sa.Boolean(), default=False, index=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("ix_business_category_status", "businesses", ["category", "status"])
    op.create_index("ix_business_phone_blacklist", "businesses", ["phone", "is_blacklisted"])

    # ── lead_analysis ─────────────────────────────────────────────────────────
    op.create_table(
        "lead_analysis",
        sa.Column(
            "business_id",
            sa.Integer(),
            sa.ForeignKey("businesses.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("lead_type", sa.String(), index=True),
        sa.Column("lead_score", sa.Integer(), default=0, index=True),
        sa.Column("ssl_enabled", sa.Boolean(), default=False),
        sa.Column("mobile_friendly", sa.Boolean(), default=False),
        sa.Column("load_time", sa.Float(), nullable=True),
        sa.Column(
            "analyzed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_lead_type_score", "lead_analysis", ["lead_type", "lead_score"])

    # ── blacklist ─────────────────────────────────────────────────────────────
    op.create_table(
        "blacklist",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("value", sa.String(), unique=True, index=True),
        sa.Column("type", sa.String(), index=True),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # ── job_logs ──────────────────────────────────────────────────────────────
    op.create_table(
        "job_logs",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column(
            "job_id",
            sa.String(),
            sa.ForeignKey("scraping_jobs.job_id", ondelete="CASCADE"),
            index=True,
        ),
        sa.Column("level", sa.String()),
        sa.Column("message", sa.Text()),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_job_log_job_level", "job_logs", ["job_id", "level"])


def downgrade() -> None:
    op.drop_table("job_logs")
    op.drop_table("blacklist")
    op.drop_table("lead_analysis")
    op.drop_table("businesses")
    op.drop_table("scraping_jobs")
