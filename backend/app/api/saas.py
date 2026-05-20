from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.billing.providers import get_provider
from app.db.session import get_db
from app.models.saas import Plan, ReportExport, Subscription, Tenant, ValuationReport
from app.models.user import User
from app.models.vehicle import Vehicle
from app.schemas.saas import CheckoutRequest
from app.services.saas_service import assert_usage_available, get_subscription_plan, monthly_usage_count

router = APIRouter(prefix="/saas", tags=["saas"])

def _require_admin(user: User):
    if getattr(user, "role", "user") != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito à operação interna")

@router.get("/meu-painel")
def meu_painel(db: Session = Depends(get_db), user: User = Depends(current_user)):
    _sub, plan = get_subscription_plan(db, user.tenant_id)
    used = monthly_usage_count(db, user.tenant_id)
    total_reports = db.query(func.count(ValuationReport.id)).filter(ValuationReport.tenant_id == user.tenant_id).scalar() or 0
    total_vehicles = db.query(func.count(Vehicle.id)).filter(Vehicle.tenant_id == user.tenant_id).scalar() or 0
    last_report = db.query(ValuationReport).filter(ValuationReport.tenant_id == user.tenant_id).order_by(ValuationReport.created_at.desc()).first()
    return {"tenant_id": user.tenant_id, "plano_atual": plan.name, "limite_laudos": plan.monthly_report_limit, "laudos_usados_mes": used, "laudos_restantes": max(plan.monthly_report_limit - used, 0), "total_laudos": total_reports, "total_veiculos": total_vehicles, "ultimo_laudo": {"id": last_report.id, "titulo": last_report.title, "valor_recomendado": last_report.recommended_value, "data": str(last_report.created_at)} if last_report else None, "modo": "Modo demonstração" if user.tenant_id == "demo-tenant" else "Conta real"}

@router.get("/meus-veiculos")
def meus_veiculos(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.query(Vehicle).filter(Vehicle.tenant_id == user.tenant_id).order_by(Vehicle.created_at.desc()).all()
    return [{"id": r.id, "veiculo": f"{r.brand} {r.model} {r.version}".strip(), "ano": r.year, "km": r.km, "cidade": r.city, "estado": r.state, "criado_em": str(r.created_at)} for r in rows]

@router.get("/meus-laudos")
def meus_laudos(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.query(ValuationReport).filter(ValuationReport.tenant_id == user.tenant_id).order_by(ValuationReport.created_at.desc()).all()
    return [{"id": r.id, "titulo": r.title, "data": str(r.created_at), "valor_recomendado": r.recommended_value, "liquidez": r.liquidity_level, "confianca": r.confidence_label, "status": r.status, "baixar_pdf": f"/api/saas/laudos/{r.id}/pdf"} for r in rows]

@router.get("/laudos/{report_id}")
def abrir_laudo(report_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    report = db.query(ValuationReport).filter(ValuationReport.id == report_id, ValuationReport.tenant_id == user.tenant_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Laudo não encontrado")
    return report.payload

@router.get("/laudos/{report_id}/pdf")
def baixar_pdf(report_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    report = db.query(ValuationReport).filter(ValuationReport.id == report_id, ValuationReport.tenant_id == user.tenant_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Laudo não encontrado")
    if not db.query(ReportExport).filter(ReportExport.report_id == report.id, ReportExport.tenant_id == user.tenant_id).first():
        db.add(ReportExport(tenant_id=user.tenant_id, report_id=report.id, export_type="pdf")); db.commit()
    return {"message": "PDF preparado pelo frontend com base no laudo salvo.", "report_id": report.id, "status": "preparado"}

@router.get("/plano-atual")
def plano_atual(db: Session = Depends(get_db), user: User = Depends(current_user)):
    sub, plan = get_subscription_plan(db, user.tenant_id)
    used = monthly_usage_count(db, user.tenant_id)
    return {"plano": plan.name, "plan_id": plan.id, "status": sub.status if sub else "ativa", "limite": plan.monthly_report_limit, "usado": used, "restante": max(plan.monthly_report_limit - used, 0)}

@router.get("/planos")
def planos(db: Session = Depends(get_db)):
    return [{"id": p.id, "nome": p.name, "limite_laudos": p.monthly_report_limit, "usuarios": p.user_limit, "descricao": p.description} for p in db.query(Plan).filter(Plan.is_active == True).all()]  # noqa: E712

@router.post("/billing/checkout")
def preparar_checkout(data: CheckoutRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    plan = db.query(Plan).filter(Plan.id == data.plan_id, Plan.is_active == True).first()  # noqa: E712
    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    session = get_provider(data.provider).create_checkout_session(user.tenant_id, data.plan_id)
    return {"provider": session.provider, "status": session.status, "message": session.message, "checkout_url": session.checkout_url, "plan_id": plan.id}

@router.post("/billing/webhook/{provider}")
def billing_webhook(provider: str, payload: dict):
    return get_provider(provider).handle_webhook(payload)

@router.get("/uso")
def uso(db: Session = Depends(get_db), user: User = Depends(current_user)):
    return assert_usage_available(db, user.tenant_id)

@router.get("/admin/operacao")
def admin_operacao(db: Session = Depends(get_db), user: User = Depends(current_user)):
    _require_admin(user)
    recent = db.query(ValuationReport).order_by(ValuationReport.created_at.desc()).limit(10).all()
    usage_by_plan = db.query(Subscription.plan_id, func.count(Subscription.id)).group_by(Subscription.plan_id).all()
    return {"total_usuarios": db.query(func.count(User.id)).scalar() or 0, "total_tenants": db.query(func.count(Tenant.id)).scalar() or 0, "laudos_gerados": db.query(func.count(ValuationReport.id)).scalar() or 0, "uso_por_plano": [{"plano": p, "quantidade": c} for p, c in usage_by_plan], "avaliacoes_recentes": [{"id": r.id, "tenant_id": r.tenant_id, "titulo": r.title, "valor": r.recommended_value, "data": str(r.created_at)} for r in recent]}
