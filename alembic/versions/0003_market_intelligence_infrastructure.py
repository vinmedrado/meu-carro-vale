"""market intelligence infrastructure

Revision ID: 0003_market_intel
Revises: 0002_real_market
Create Date: 2026-05-18
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_market_intel"
down_revision = "0002_real_market"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("market_listings") as batch:
        batch.add_column(sa.Column("seller_type", sa.String(length=40), nullable=False, server_default=""))
        batch.add_column(sa.Column("fingerprint", sa.String(length=80), nullable=False, server_default=""))
        batch.add_column(sa.Column("duplicate_score", sa.Integer(), nullable=False, server_default="0"))
        batch.add_column(sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")))
    op.create_index("ix_market_listings_fingerprint", "market_listings", ["fingerprint"])
    op.create_index("ix_market_listings_duplicate_score", "market_listings", ["duplicate_score"])

    op.create_table("market_listing_history", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("market_listing_id", sa.Integer(), nullable=False), sa.Column("price", sa.Float(), nullable=False), sa.Column("mileage", sa.Integer(), nullable=False, server_default="0"), sa.Column("source", sa.String(length=60), nullable=False, server_default=""), sa.Column("raw", sa.JSON(), nullable=False), sa.Column("captured_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")))
    op.create_index("ix_market_listing_history_market_listing_id", "market_listing_history", ["market_listing_id"])
    op.create_index("ix_market_listing_history_captured_at", "market_listing_history", ["captured_at"])

    op.create_table("market_snapshots", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("snapshot_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")), sa.Column("total_listings", sa.Integer(), nullable=False, server_default="0"), sa.Column("active_listings", sa.Integer(), nullable=False, server_default="0"), sa.Column("payload", sa.JSON(), nullable=False))
    op.create_index("ix_market_snapshots_snapshot_at", "market_snapshots", ["snapshot_at"])

    op.create_table("market_price_stats", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("brand", sa.String(length=90), nullable=False), sa.Column("model", sa.String(length=140), nullable=False), sa.Column("year", sa.Integer(), nullable=False), sa.Column("state", sa.String(length=2), nullable=False, server_default=""), sa.Column("listing_count", sa.Integer(), nullable=False, server_default="0"), sa.Column("p25", sa.Float(), nullable=False, server_default="0"), sa.Column("p50", sa.Float(), nullable=False, server_default="0"), sa.Column("p75", sa.Float(), nullable=False, server_default="0"), sa.Column("avg_price", sa.Float(), nullable=False, server_default="0"), sa.Column("min_price", sa.Float(), nullable=False, server_default="0"), sa.Column("max_price", sa.Float(), nullable=False, server_default="0"), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")))
    for col in ["brand", "model", "year", "state", "created_at"]:
        op.create_index(f"ix_market_price_stats_{col}", "market_price_stats", [col])

    op.create_table("market_liquidity", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("brand", sa.String(length=90), nullable=False), sa.Column("model", sa.String(length=140), nullable=False), sa.Column("year", sa.Integer(), nullable=False), sa.Column("state", sa.String(length=2), nullable=False, server_default=""), sa.Column("listing_count", sa.Integer(), nullable=False, server_default="0"), sa.Column("liquidity_score", sa.Integer(), nullable=False, server_default="0"), sa.Column("liquidity_label", sa.String(length=30), nullable=False, server_default="Baixa"), sa.Column("dispersion", sa.Float(), nullable=False, server_default="0"), sa.Column("regional_volume", sa.Integer(), nullable=False, server_default="0"), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")))
    for col in ["brand", "model", "year", "state", "created_at"]:
        op.create_index(f"ix_market_liquidity_{col}", "market_liquidity", [col])

    op.create_table("market_collection_jobs", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("source", sa.String(length=60), nullable=False), sa.Column("status", sa.String(length=30), nullable=False, server_default="queued"), sa.Column("params", sa.JSON(), nullable=False), sa.Column("imported_count", sa.Integer(), nullable=False, server_default="0"), sa.Column("duplicate_count", sa.Integer(), nullable=False, server_default="0"), sa.Column("error_count", sa.Integer(), nullable=False, server_default="0"), sa.Column("error_message", sa.Text(), nullable=False, server_default=""), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")), sa.Column("started_at", sa.DateTime(timezone=True), nullable=True), sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True))
    for col in ["source", "status", "created_at"]:
        op.create_index(f"ix_market_collection_jobs_{col}", "market_collection_jobs", [col])


def downgrade():
    op.drop_table("market_collection_jobs")
    op.drop_table("market_liquidity")
    op.drop_table("market_price_stats")
    op.drop_table("market_snapshots")
    op.drop_table("market_listing_history")
    with op.batch_alter_table("market_listings") as batch:
        batch.drop_column("is_active")
        batch.drop_column("duplicate_score")
        batch.drop_column("fingerprint")
        batch.drop_column("seller_type")
