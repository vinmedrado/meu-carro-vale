"""vehicle catalog master

Revision ID: 0004_vehicle_catalog
Revises: 0003_market_intel
Create Date: 2026-05-18
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_vehicle_catalog"
down_revision = "0003_market_intel"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("vehicle_brands", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("vehicle_type", sa.String(length=20), nullable=False), sa.Column("canonical_name", sa.String(length=100), nullable=False), sa.Column("fipe_code", sa.String(length=40), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")), sa.UniqueConstraint("vehicle_type", "fipe_code", name="uq_vehicle_brand_type_fipe"))
    for col in ["id", "vehicle_type", "canonical_name", "fipe_code", "is_active"]: op.create_index(f"ix_vehicle_brands_{col}", "vehicle_brands", [col])
    op.create_table("vehicle_brand_aliases", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("brand_id", sa.Integer(), sa.ForeignKey("vehicle_brands.id"), nullable=False), sa.Column("alias", sa.String(length=120), nullable=False), sa.Column("source", sa.String(length=60), nullable=False, server_default="manual"), sa.UniqueConstraint("brand_id", "alias", name="uq_vehicle_brand_alias"))
    for col in ["id", "brand_id", "alias"]: op.create_index(f"ix_vehicle_brand_aliases_{col}", "vehicle_brand_aliases", [col])
    op.create_table("vehicle_models", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("brand_id", sa.Integer(), sa.ForeignKey("vehicle_brands.id"), nullable=False), sa.Column("canonical_name", sa.String(length=160), nullable=False), sa.Column("fipe_code", sa.String(length=40), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")), sa.UniqueConstraint("brand_id", "fipe_code", name="uq_vehicle_model_brand_fipe"))
    for col in ["id", "brand_id", "canonical_name", "fipe_code", "is_active"]: op.create_index(f"ix_vehicle_models_{col}", "vehicle_models", [col])
    op.create_index("ix_vehicle_models_brand_name", "vehicle_models", ["brand_id", "canonical_name"])
    op.create_table("vehicle_model_aliases", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("model_id", sa.Integer(), sa.ForeignKey("vehicle_models.id"), nullable=False), sa.Column("alias", sa.String(length=180), nullable=False), sa.Column("source", sa.String(length=60), nullable=False, server_default="manual"), sa.UniqueConstraint("model_id", "alias", name="uq_vehicle_model_alias"))
    for col in ["id", "model_id", "alias"]: op.create_index(f"ix_vehicle_model_aliases_{col}", "vehicle_model_aliases", [col])
    op.create_table("vehicle_versions", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("model_id", sa.Integer(), sa.ForeignKey("vehicle_models.id"), nullable=False), sa.Column("fipe_year_code", sa.String(length=40), nullable=False), sa.Column("year", sa.Integer(), nullable=False), sa.Column("fuel", sa.String(length=50), nullable=False, server_default=""), sa.Column("version_name", sa.String(length=220), nullable=False, server_default=""), sa.Column("fipe_code", sa.String(length=40), nullable=False, server_default=""), sa.Column("reference_month", sa.String(length=80), nullable=False, server_default=""), sa.Column("fipe_price", sa.Float(), nullable=False, server_default="0"), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")), sa.UniqueConstraint("model_id", "fipe_year_code", "reference_month", name="uq_vehicle_version_model_year_ref"))
    for col in ["id", "model_id", "fipe_year_code", "year", "fuel", "version_name", "fipe_code", "reference_month"]: op.create_index(f"ix_vehicle_versions_{col}", "vehicle_versions", [col])
    op.create_table("vehicle_catalog_sync_logs", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("status", sa.String(length=30), nullable=False), sa.Column("vehicle_type", sa.String(length=20), nullable=False, server_default="all"), sa.Column("brands_count", sa.Integer(), nullable=False, server_default="0"), sa.Column("models_count", sa.Integer(), nullable=False, server_default="0"), sa.Column("versions_count", sa.Integer(), nullable=False, server_default="0"), sa.Column("error_message", sa.Text(), nullable=False, server_default=""), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")))
    for col in ["id", "status", "vehicle_type", "created_at"]: op.create_index(f"ix_vehicle_catalog_sync_logs_{col}", "vehicle_catalog_sync_logs", [col])


def downgrade():
    op.drop_table("vehicle_catalog_sync_logs")
    op.drop_table("vehicle_versions")
    op.drop_table("vehicle_model_aliases")
    op.drop_table("vehicle_models")
    op.drop_table("vehicle_brand_aliases")
    op.drop_table("vehicle_brands")
