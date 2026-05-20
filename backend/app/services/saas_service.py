from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from uuid import uuid4
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.saas import Plan, RefreshToken, Subscription, Tenant, TenantUser, UsageEvent
from app.models.user import User


def current_period() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def token_digest(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def create_tenant_for_user(db: Session, user: User, tenant_name: str | None = None, tenant_type: str = "usuario_individual") -> Tenant:
    tenant_id = f"tenant-{uuid4().hex[:12]}"
    tenant = Tenant(id=tenant_id, name=tenant_name or f"Espaço de {user.name}", tenant_type=tenant_type)
    user.tenant_id = tenant_id
    user.role = "owner"
    db.add(tenant)
    db.flush()
    db.add(TenantUser(tenant_id=tenant_id, user_id=user.id, role="owner"))
    db.add(Subscription(tenant_id=tenant_id, plan_id="avulso", status="ativa", current_period=current_period()))
    db.commit()
    db.refresh(user)
    return tenant


def ensure_demo_tenant(db: Session, user: User) -> None:
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    if not tenant:
        db.add(Tenant(id=user.tenant_id, name="Demonstração Meu Carro Vale", tenant_type="demo"))
    if not db.query(TenantUser).filter(TenantUser.tenant_id == user.tenant_id, TenantUser.user_id == user.id).first():
        db.add(TenantUser(tenant_id=user.tenant_id, user_id=user.id, role="owner"))
    if not db.query(Subscription).filter(Subscription.tenant_id == user.tenant_id).first():
        db.add(Subscription(tenant_id=user.tenant_id, plan_id="profissional", status="demo", current_period=current_period()))
    db.commit()


def get_subscription_plan(db: Session, tenant_id: str) -> tuple[Subscription | None, Plan]:
    sub = db.query(Subscription).filter(Subscription.tenant_id == tenant_id).order_by(Subscription.id.desc()).first()
    plan_id = sub.plan_id if sub else "avulso"
    plan = db.query(Plan).filter(Plan.id == plan_id).first() or db.query(Plan).filter(Plan.id == "avulso").first()
    if not plan:
        plan = Plan(id="avulso", name="Plano Avulso", monthly_report_limit=1, user_limit=1)
        db.add(plan); db.commit()
    return sub, plan


def monthly_usage_count(db: Session, tenant_id: str, event_type: str = "laudo_gerado") -> int:
    return int(db.query(func.count(UsageEvent.id)).filter(
        UsageEvent.tenant_id == tenant_id,
        UsageEvent.event_type == event_type,
        UsageEvent.period == current_period(),
    ).scalar() or 0)


def assert_usage_available(db: Session, tenant_id: str) -> dict:
    _sub, plan = get_subscription_plan(db, tenant_id)
    used = monthly_usage_count(db, tenant_id)
    limit = plan.monthly_report_limit
    if limit >= 0 and used >= limit:
        raise HTTPException(status_code=402, detail="Você atingiu o limite do plano atual.")
    return {"plan_id": plan.id, "plan_name": plan.name, "used": used, "limit": limit, "remaining": max(limit - used, 0)}


def record_usage(db: Session, tenant_id: str, user_id: int, metadata: dict | None = None) -> UsageEvent:
    event = UsageEvent(tenant_id=tenant_id, user_id=user_id, event_type="laudo_gerado", period=current_period(), metadata_json=metadata or {})
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
