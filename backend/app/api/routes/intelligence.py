from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.db.session import get_db
from app.intelligence.providers.registry import registry
from app.models.market import MarketListing, MarketSnapshot
from app.models.user import User

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


@router.get("/overview")
def intelligence_overview(db: Session = Depends(get_db), user: User = Depends(current_user)):
    total = db.query(MarketListing).count()
    active = db.query(MarketListing).filter(MarketListing.is_active == True).count()  # noqa: E712
    latest_snapshot = db.query(MarketSnapshot).order_by(MarketSnapshot.snapshot_at.desc()).first()
    return {
        "engine": "MCV Market Intelligence Engine",
        "version": "2.0",
        "enabled_layers": [
            "Market Live Data Engine",
            "Comparable Engine",
            "Liquidity Engine",
            "Negotiation Engine",
            "Confidence Engine",
            "Regional Engine",
            "Market Trend Engine",
            "Selling Strategy Engine",
            "Price Positioning Engine",
            "Buyer Behavior Engine",
            "Market Insight Engine",
            "Liquidity Pressure Engine",
        ],
        "provider_contracts": ["OLX", "Webmotors", "iCarros", "Kavak", "FIPE", "CSV autorizado"],
        "registered_providers": registry.enabled_sources(),
        "market_base": {"total_listings": total, "active_listings": active},
        "latest_snapshot": {
            "id": latest_snapshot.id,
            "snapshot_at": str(latest_snapshot.snapshot_at),
            "payload": latest_snapshot.payload,
        } if latest_snapshot else None,
        "safety_note": "Coletores externos devem usar APIs, CSVs autorizados ou integrações permitidas. Scraping agressivo não é habilitado por padrão.",
    }
