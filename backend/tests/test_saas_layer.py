from app.models.saas import Plan, Subscription, Tenant, TenantUser, UsageEvent, ValuationReport
from app.models.user import User
from app.services.saas_service import create_tenant_for_user, assert_usage_available, record_usage, get_subscription_plan


def test_create_tenant_for_user(db_session):
    db_session.add(Plan(id="avulso", name="Plano Avulso", monthly_report_limit=1, user_limit=1))
    user = User(name="Vinicius", email="vini@example.com", password_hash="hash", tenant_id="pending")
    db_session.add(user); db_session.commit(); db_session.refresh(user)
    tenant = create_tenant_for_user(db_session, user, "Minha loja")
    assert tenant.id == user.tenant_id
    assert db_session.query(TenantUser).filter_by(tenant_id=tenant.id, user_id=user.id).first()
    assert db_session.query(Subscription).filter_by(tenant_id=tenant.id).first()


def test_usage_limit_blocks_second_report(db_session):
    db_session.add(Plan(id="avulso", name="Plano Avulso", monthly_report_limit=1, user_limit=1))
    user = User(name="Ana", email="ana@example.com", password_hash="hash", tenant_id="pending")
    db_session.add(user); db_session.commit(); db_session.refresh(user)
    create_tenant_for_user(db_session, user, "Conta Ana")
    available = assert_usage_available(db_session, user.tenant_id)
    assert available["remaining"] == 1
    record_usage(db_session, user.tenant_id, user.id, {"report_id": 1})
    try:
        assert_usage_available(db_session, user.tenant_id)
        assert False, "limite deveria bloquear"
    except Exception as exc:
        assert "limite" in str(exc).lower()


def test_tenant_report_isolation(db_session):
    db_session.add(Plan(id="avulso", name="Plano Avulso", monthly_report_limit=3, user_limit=1))
    u1 = User(name="Loja A", email="a@example.com", password_hash="x", tenant_id="pending")
    u2 = User(name="Loja B", email="b@example.com", password_hash="x", tenant_id="pending")
    db_session.add_all([u1, u2]); db_session.commit(); db_session.refresh(u1); db_session.refresh(u2)
    create_tenant_for_user(db_session, u1, "A")
    create_tenant_for_user(db_session, u2, "B")
    db_session.add(ValuationReport(tenant_id=u1.tenant_id, user_id=u1.id, title="Laudo A", payload={}))
    db_session.add(ValuationReport(tenant_id=u2.tenant_id, user_id=u2.id, title="Laudo B", payload={}))
    db_session.commit()
    rows = db_session.query(ValuationReport).filter(ValuationReport.tenant_id == u1.tenant_id).all()
    assert len(rows) == 1
    assert rows[0].title == "Laudo A"
