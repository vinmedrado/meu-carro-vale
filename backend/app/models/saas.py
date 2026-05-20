from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


def now_utc():
    return datetime.now(timezone.utc)


class Tenant(Base):
    __tablename__ = "tenants"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    tenant_type: Mapped[str] = mapped_column(String(40), default="usuario_individual")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Role(Base):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(180), default="")


class TenantUser(Base):
    __tablename__ = "tenant_users"
    __table_args__ = (UniqueConstraint("tenant_id", "user_id", name="uq_tenant_user"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), ForeignKey("tenants.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str] = mapped_column(String(40), default="owner", index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class Plan(Base):
    __tablename__ = "plans"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    monthly_report_limit: Mapped[int] = mapped_column(Integer, default=1)
    user_limit: Mapped[int] = mapped_column(Integer, default=1)
    description: Mapped[str] = mapped_column(Text, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Subscription(Base):
    __tablename__ = "subscriptions"
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), ForeignKey("tenants.id"), index=True)
    plan_id: Mapped[str] = mapped_column(String(40), ForeignKey("plans.id"), index=True, default="avulso")
    status: Mapped[str] = mapped_column(String(40), default="ativa")
    provider: Mapped[str] = mapped_column(String(40), default="manual")
    current_period: Mapped[str] = mapped_column(String(7), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class UsageEvent(Base):
    __tablename__ = "usage_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(60), default="laudo_gerado", index=True)
    period: Mapped[str] = mapped_column(String(7), index=True)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class ValuationReport(Base):
    __tablename__ = "valuation_reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    vehicle_id: Mapped[int | None] = mapped_column(ForeignKey("vehicles.id"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(180), default="Laudo Meu Carro Vale")
    status: Mapped[str] = mapped_column(String(40), default="concluido")
    recommended_value: Mapped[float] = mapped_column(Float, default=0)
    liquidity_level: Mapped[str] = mapped_column(String(60), default="Não informado")
    confidence_label: Mapped[str] = mapped_column(String(60), default="Não informado")
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, index=True)


class ReportExport(Base):
    __tablename__ = "report_exports"
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("valuation_reports.id"), index=True)
    export_type: Mapped[str] = mapped_column(String(20), default="pdf")
    status: Mapped[str] = mapped_column(String(40), default="preparado")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(255), index=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
