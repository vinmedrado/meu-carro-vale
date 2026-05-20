"""MCV Intelligence Engine tables

Revision ID: 0006_mcv_intelligence_engine
Revises: 0005_vehicle_catalog_sync_jobs
Create Date: 2026-05-18
"""
from alembic import op
import sqlalchemy as sa

revision = "0006_mcv_intelligence_engine"
down_revision = "0005_vehicle_catalog_sync_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "comparable_vehicles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("valuation_run_id", sa.Integer(), nullable=True),
        sa.Column("market_listing_id", sa.Integer(), nullable=True),
        sa.Column("brand", sa.String(90), nullable=False, server_default=""),
        sa.Column("model", sa.String(140), nullable=False, server_default=""),
        sa.Column("version", sa.String(160), nullable=False, server_default=""),
        sa.Column("year", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("mileage", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("state", sa.String(2), nullable=False, server_default=""),
        sa.Column("source", sa.String(60), nullable=False, server_default=""),
        sa.Column("price", sa.Float(), nullable=False, server_default="0"),
        sa.Column("similarity_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("regional_similarity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("km_similarity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("market_distance", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_comparable_lookup", "comparable_vehicles", ["brand", "model", "year", "state", "similarity_score"])
    op.create_table(
        "valuation_confidence",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("valuation_run_id", sa.Integer(), nullable=True),
        sa.Column("confidence_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("confidence_level", sa.String(30), nullable=False, server_default="Baixa"),
        sa.Column("confidence_reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("analysis_quality", sa.String(40), nullable=False, server_default="exploratória"),
        sa.Column("comparable_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("dispersion", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "negotiation_ranges",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("valuation_run_id", sa.Integer(), nullable=True),
        sa.Column("quick_sale_price", sa.Float(), nullable=False, server_default="0"),
        sa.Column("recommended_price", sa.Float(), nullable=False, server_default="0"),
        sa.Column("negotiation_floor", sa.Float(), nullable=False, server_default="0"),
        sa.Column("negotiation_ceiling", sa.Float(), nullable=False, server_default="0"),
        sa.Column("estimated_negotiation_margin", sa.Float(), nullable=False, server_default="0"),
        sa.Column("positioning", sa.String(40), nullable=False, server_default="equilibrado"),
        sa.Column("payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        "regional_valuation",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("brand", sa.String(90), nullable=False, server_default=""),
        sa.Column("model", sa.String(140), nullable=False, server_default=""),
        sa.Column("year", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("state", sa.String(2), nullable=False, server_default=""),
        sa.Column("regional_multiplier", sa.Float(), nullable=False, server_default="1"),
        sa.Column("regional_market_temperature", sa.String(40), nullable=False, server_default="Equilibrado"),
        sa.Column("regional_price_delta", sa.Float(), nullable=False, server_default="0"),
        sa.Column("sample_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_regional_valuation_lookup", "regional_valuation", ["brand", "model", "year", "state"])
    op.create_table(
        "market_trends",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("brand", sa.String(90), nullable=False, server_default=""),
        sa.Column("model", sa.String(140), nullable=False, server_default=""),
        sa.Column("year", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("state", sa.String(2), nullable=False, server_default=""),
        sa.Column("trend_direction", sa.String(30), nullable=False, server_default="estável"),
        sa.Column("weekly_trend", sa.String(30), nullable=False, server_default="monitorar"),
        sa.Column("monthly_trend", sa.String(30), nullable=False, server_default="monitorar"),
        sa.Column("price_spread", sa.Float(), nullable=False, server_default="0"),
        sa.Column("payload", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_market_trend_lookup", "market_trends", ["brand", "model", "year", "state", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_market_trend_lookup", table_name="market_trends")
    op.drop_table("market_trends")
    op.drop_index("ix_regional_valuation_lookup", table_name="regional_valuation")
    op.drop_table("regional_valuation")
    op.drop_table("negotiation_ranges")
    op.drop_table("valuation_confidence")
    op.drop_index("ix_comparable_lookup", table_name="comparable_vehicles")
    op.drop_table("comparable_vehicles")
