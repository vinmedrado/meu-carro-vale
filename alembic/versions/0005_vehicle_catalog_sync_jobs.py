"""vehicle catalog async sync jobs

Revision ID: 0005_vehicle_catalog_jobs
Revises: 0004_vehicle_catalog
Create Date: 2026-05-18
"""
from alembic import op
import sqlalchemy as sa

revision = "0005_vehicle_catalog_jobs"
down_revision = "0004_vehicle_catalog"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "vehicle_catalog_sync_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("vehicle_type", sa.String(length=20), nullable=False, server_default="all"),
        sa.Column("total_brands", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_brands", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_models", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_models", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_versions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_versions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    for col in ["id", "status", "vehicle_type", "created_at"]:
        op.create_index(f"ix_vehicle_catalog_sync_jobs_{col}", "vehicle_catalog_sync_jobs", [col])


def downgrade():
    op.drop_table("vehicle_catalog_sync_jobs")
