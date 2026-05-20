from __future__ import annotations

from app.db.session import Base, SessionLocal, engine

# IMPORTANTE: estes imports registram todos os models no Base.metadata
from app.models.user import User  # noqa: F401
from app.models.vehicle import Vehicle  # noqa: F401
from app.models.market import (  # noqa: F401
    FipePrice,
    MarketCollectionJob,
    MarketLiquidity,
    MarketListing,
    MarketListingHistory,
    MarketPriceStats,
    MarketSnapshot,
    ValuationComparable,
    ValuationRun,
    ComparableVehicle,
    ValuationConfidence,
    NegotiationRange,
    RegionalValuation,
    MarketTrend,
)

from app.models.saas import (  # noqa: F401
    Plan,
    RefreshToken,
    ReportExport,
    Role,
    Subscription,
    Tenant,
    TenantUser,
    UsageEvent,
    ValuationReport,
)
from app.vehicle_catalog.models import (  # noqa: F401
    VehicleBrand,
    VehicleBrandAlias,
    VehicleCatalogSyncJob,
    VehicleCatalogSyncLog,
    VehicleModel,
    VehicleModelAlias,
    VehicleVersion,
)
from app.vehicle_catalog.services.catalog_service import VehicleCatalogService


def seed_saas_defaults(db):
    default_roles = {
        "admin": "Operação interna",
        "owner": "Responsável pelo espaço",
        "analyst": "Analista de avaliações",
        "user": "Consulta de laudos",
    }
    for name, description in default_roles.items():
        if not db.query(Role).filter(Role.name == name).first():
            db.add(Role(name=name, description=description))

    plans = [
        Plan(id="avulso", name="Plano Avulso", monthly_report_limit=1, user_limit=1, description="1 laudo por compra avulsa"),
        Plan(id="pessoal", name="Plano Pessoal", monthly_report_limit=5, user_limit=1, description="Uso individual com histórico"),
        Plan(id="lojista", name="Plano Lojista", monthly_report_limit=40, user_limit=3, description="Loja pequena com comparáveis e histórico"),
        Plan(id="profissional", name="Plano Profissional", monthly_report_limit=150, user_limit=10, description="Equipe comercial com múltiplos usuários"),
    ]
    for plan in plans:
        if not db.query(Plan).filter(Plan.id == plan.id).first():
            db.add(plan)
    db.commit()


def init_database(seed_catalog: bool = True) -> None:
    """Cria as tabelas locais e garante um catálogo mínimo para uso em demo/local.

    O projeto também possui Alembic na raiz, mas este inicializador deixa o app
    utilizável mesmo quando o usuário roda apenas o backend local em SQLite.
    """
    Base.metadata.create_all(bind=engine)

    if seed_catalog:
        db = SessionLocal()
        try:
            seed_saas_defaults(db)
            VehicleCatalogService().ensure_manual_alias_catalog(db, vehicle_type="carros")
        finally:
            db.close()


if __name__ == "__main__":
    init_database()
    print("Database ready")
