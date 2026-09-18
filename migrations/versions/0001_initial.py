"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-09-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "brands",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("kit", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "products",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("brand_id", sa.String(64), sa.ForeignKey("brands.id", ondelete="CASCADE")),
        sa.Column("sku", sa.String(128), nullable=False),
        sa.Column("title", sa.String(400), nullable=False),
        sa.Column("attrs", sa.JSON(), nullable=False),
        sa.Column("source_images", sa.JSON(), nullable=True),
        sa.UniqueConstraint("brand_id", "sku", name="uq_product_brand_sku"),
    )
    op.create_table(
        "jobs",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("product_id", sa.String(64), sa.ForeignKey("products.id", ondelete="CASCADE")),
        sa.Column("brand_id", sa.String(64), sa.ForeignKey("brands.id")),
        sa.Column("status", sa.String(32), server_default="queued"),
        sa.Column("mode", sa.String(8), server_default="mock"),
        sa.Column("channels", sa.JSON(), nullable=False),
        sa.Column("budget_cents", sa.Integer(), server_default="250"),
        sa.Column("spent_cents", sa.Integer(), server_default="0"),
        sa.Column("approval_required", sa.Boolean(), server_default=sa.true()),
        sa.Column("thread_id", sa.String(64), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_jobs_status", "jobs", ["status"])
    op.create_table(
        "runs",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("job_id", sa.String(64), sa.ForeignKey("jobs.id", ondelete="CASCADE")),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("trigger", sa.String(16), nullable=False),
        sa.Column("regen_keys", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("job_id", "version"),
    )
    op.create_table(
        "assets",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("job_id", sa.String(64), sa.ForeignKey("jobs.id", ondelete="CASCADE")),
        sa.Column("run_id", sa.String(64), sa.ForeignKey("runs.id", ondelete="CASCADE")),
        sa.Column("key", sa.String(128), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("channel", sa.String(32), nullable=False),
        sa.Column("variant", sa.String(16), server_default="a"),
        sa.Column("locale", sa.String(8), server_default="en"),
        sa.Column("uri", sa.Text(), nullable=False),
        sa.Column("content", sa.JSON(), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(16), server_default="draft"),
        sa.Column("superseded_by", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "qa_reports",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("asset_id", sa.String(64), sa.ForeignKey("assets.id", ondelete="CASCADE")),
        sa.Column("job_id", sa.String(64), sa.ForeignKey("jobs.id", ondelete="CASCADE")),
        sa.Column("verdict", sa.String(8), nullable=False),
        sa.Column("judge", sa.String(16), nullable=False),
        sa.Column("checks", sa.JSON(), nullable=False),
        sa.Column("cost_cents", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "publish_attempts",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("asset_id", sa.String(64), sa.ForeignKey("assets.id", ondelete="CASCADE")),
        sa.Column("job_id", sa.String(64), sa.ForeignKey("jobs.id", ondelete="CASCADE")),
        sa.Column("platform", sa.String(32), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("external_id", sa.String(200), nullable=True),
        sa.Column("external_url", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("idempotency_key", name="uq_publish_idem"),
    )
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("job_id", sa.String(64), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("type", sa.String(48), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
    )
    op.create_index("ix_events_job_id", "events", ["job_id"])
    op.create_index("ix_events_type", "events", ["type"])
    op.create_table(
        "metric_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("asset_id", sa.String(64), sa.ForeignKey("assets.id", ondelete="CASCADE")),
        sa.Column("platform", sa.String(32), nullable=False),
        sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("metrics", sa.JSON(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("metric_snapshots")
    op.drop_table("events")
    op.drop_table("publish_attempts")
    op.drop_table("qa_reports")
    op.drop_table("assets")
    op.drop_table("runs")
    op.drop_table("jobs")
    op.drop_table("products")
    op.drop_table("brands")
