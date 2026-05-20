"""SaaS commercial layer

Revision ID: 0007_saas_commercial
Revises: 0006_mcv_intelligence_engine
Create Date: 2026-05-19
"""
from alembic import op
import sqlalchemy as sa

revision = "0007_saas_commercial"
down_revision = "0006_mcv_intelligence_engine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("role", sa.String(length=40), nullable=False, server_default="owner"))
    op.create_index("ix_users_role", "users", ["role"])

    op.create_table("tenants", sa.Column("id", sa.String(64), primary_key=True), sa.Column("name", sa.String(160), nullable=False), sa.Column("tenant_type", sa.String(40), nullable=False, server_default="usuario_individual"), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")))
    op.create_index("ix_tenants_name", "tenants", ["name"])
    op.create_table("roles", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("name", sa.String(40), nullable=False, unique=True), sa.Column("description", sa.String(180), nullable=False, server_default=""))
    op.create_index("ix_roles_name", "roles", ["name"])
    op.create_table("tenant_users", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("tenant_id", sa.String(64), sa.ForeignKey("tenants.id"), nullable=False), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), sa.Column("role", sa.String(40), nullable=False, server_default="owner"), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")), sa.UniqueConstraint("tenant_id", "user_id", name="uq_tenant_user"))
    op.create_index("ix_tenant_users_tenant_id", "tenant_users", ["tenant_id"])
    op.create_index("ix_tenant_users_user_id", "tenant_users", ["user_id"])
    op.create_index("ix_tenant_users_role", "tenant_users", ["role"])
    op.create_table("plans", sa.Column("id", sa.String(40), primary_key=True), sa.Column("name", sa.String(80), nullable=False), sa.Column("monthly_report_limit", sa.Integer(), nullable=False, server_default="1"), sa.Column("user_limit", sa.Integer(), nullable=False, server_default="1"), sa.Column("description", sa.Text(), nullable=False, server_default=""), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")))
    op.create_table("subscriptions", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("tenant_id", sa.String(64), sa.ForeignKey("tenants.id"), nullable=False), sa.Column("plan_id", sa.String(40), sa.ForeignKey("plans.id"), nullable=False, server_default="avulso"), sa.Column("status", sa.String(40), nullable=False, server_default="ativa"), sa.Column("provider", sa.String(40), nullable=False, server_default="manual"), sa.Column("current_period", sa.String(7), nullable=False, server_default=""), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")))
    op.create_index("ix_subscriptions_tenant_id", "subscriptions", ["tenant_id"])
    op.create_index("ix_subscriptions_plan_id", "subscriptions", ["plan_id"])
    op.create_table("usage_events", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("tenant_id", sa.String(64), nullable=False), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), sa.Column("event_type", sa.String(60), nullable=False, server_default="laudo_gerado"), sa.Column("period", sa.String(7), nullable=False), sa.Column("metadata_json", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")))
    for col in ["tenant_id", "user_id", "event_type", "period"]: op.create_index(f"ix_usage_events_{col}", "usage_events", [col])
    op.create_table("valuation_reports", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("tenant_id", sa.String(64), nullable=False), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), sa.Column("vehicle_id", sa.Integer(), sa.ForeignKey("vehicles.id"), nullable=True), sa.Column("title", sa.String(180), nullable=False, server_default="Laudo Meu Carro Vale"), sa.Column("status", sa.String(40), nullable=False, server_default="concluido"), sa.Column("recommended_value", sa.Float(), nullable=False, server_default="0"), sa.Column("liquidity_level", sa.String(60), nullable=False, server_default="Não informado"), sa.Column("confidence_label", sa.String(60), nullable=False, server_default="Não informado"), sa.Column("payload", sa.JSON(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")))
    for col in ["tenant_id", "user_id", "vehicle_id", "created_at"]: op.create_index(f"ix_valuation_reports_{col}", "valuation_reports", [col])
    op.create_table("report_exports", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("tenant_id", sa.String(64), nullable=False), sa.Column("report_id", sa.Integer(), sa.ForeignKey("valuation_reports.id"), nullable=False), sa.Column("export_type", sa.String(20), nullable=False, server_default="pdf"), sa.Column("status", sa.String(40), nullable=False, server_default="preparado"), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")))
    op.create_index("ix_report_exports_tenant_id", "report_exports", ["tenant_id"])
    op.create_index("ix_report_exports_report_id", "report_exports", ["report_id"])
    op.create_table("refresh_tokens", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("tenant_id", sa.String(64), nullable=False), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), sa.Column("token_hash", sa.String(255), nullable=False), sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.text("0")), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")))
    for col in ["tenant_id", "user_id", "token_hash"]: op.create_index(f"ix_refresh_tokens_{col}", "refresh_tokens", [col])


def downgrade() -> None:
    op.drop_table("refresh_tokens")
    op.drop_table("report_exports")
    op.drop_table("valuation_reports")
    op.drop_table("usage_events")
    op.drop_table("subscriptions")
    op.drop_table("plans")
    op.drop_table("tenant_users")
    op.drop_table("roles")
    op.drop_table("tenants")
    op.drop_index("ix_users_role", table_name="users")
    with op.batch_alter_table("users") as batch:
        batch.drop_column("role")
