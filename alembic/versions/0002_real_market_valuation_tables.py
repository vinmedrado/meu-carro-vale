"""real market valuation tables

Revision ID: 0002_real_market
Revises:
Create Date: 2026-05-18
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_real_market"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "fipe_prices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vehicle_type", sa.String(length=20), nullable=False),
        sa.Column("brand", sa.String(length=90), nullable=False),
        sa.Column("model", sa.String(length=140), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("fipe_code", sa.String(length=40), nullable=False),
        sa.Column("fuel", sa.String(length=50), nullable=False),
        sa.Column("reference_month", sa.String(length=80), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("raw", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("vehicle_type", "fipe_code", "year", "fuel", name="uq_fipe_vehicle_code_year_fuel"),
    )
    for col in ["id", "vehicle_type", "brand", "model", "year", "fipe_code"]:
        op.create_index(f"ix_fipe_prices_{col}", "fipe_prices", [col])

    op.create_table(
        "market_listings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("brand", sa.String(length=90), nullable=False),
        sa.Column("model", sa.String(length=140), nullable=False),
        sa.Column("version", sa.String(length=160), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("mileage", sa.Integer(), nullable=False),
        sa.Column("city", sa.String(length=90), nullable=False),
        sa.Column("state", sa.String(length=2), nullable=False),
        sa.Column("transmission", sa.String(length=50), nullable=False),
        sa.Column("fuel", sa.String(length=50), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=60), nullable=False),
        sa.Column("normalized_key", sa.String(length=500), nullable=False),
        sa.Column("raw", sa.JSON(), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
    )
    for col in ["id", "title", "price", "brand", "model", "year", "mileage", "state", "source", "normalized_key", "collected_at"]:
        op.create_index(f"ix_market_listings_{col}", "market_listings", [col])
    op.create_index("ix_market_lookup", "market_listings", ["brand", "model", "year", "state", "mileage", "source", "collected_at"])

    op.create_table(
        "valuation_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tenant_id", sa.String(length=64), nullable=False),
        sa.Column("app_mode", sa.String(length=20), nullable=False),
        sa.Column("brand", sa.String(length=90), nullable=False),
        sa.Column("model", sa.String(length=140), nullable=False),
        sa.Column("version", sa.String(length=160), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("mileage", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(length=2), nullable=False),
        sa.Column("fipe_value", sa.Float(), nullable=True),
        sa.Column("quick_sale_price", sa.Float(), nullable=False),
        sa.Column("ideal_price", sa.Float(), nullable=False),
        sa.Column("premium_price", sa.Float(), nullable=False),
        sa.Column("confidence_score", sa.Integer(), nullable=False),
        sa.Column("confidence_label", sa.String(length=30), nullable=False),
        sa.Column("comparable_count", sa.Integer(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
    )
    for col in ["id", "tenant_id", "app_mode", "brand", "model", "year", "state", "created_at"]:
        op.create_index(f"ix_valuation_runs_{col}", "valuation_runs", [col])

    op.create_table(
        "valuation_comparables",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("valuation_run_id", sa.Integer(), nullable=False),
        sa.Column("market_listing_id", sa.Integer(), nullable=False),
        sa.Column("similarity_score", sa.Integer(), nullable=False),
        sa.Column("adjustments", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
    )
    for col in ["id", "valuation_run_id", "market_listing_id", "similarity_score"]:
        op.create_index(f"ix_valuation_comparables_{col}", "valuation_comparables", [col])


def downgrade():
    op.drop_table("valuation_comparables")
    op.drop_table("valuation_runs")
    op.drop_table("market_listings")
    op.drop_table("fipe_prices")
