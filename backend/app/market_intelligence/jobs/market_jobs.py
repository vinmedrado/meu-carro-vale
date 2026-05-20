from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.market import MarketCollectionJob, MarketListing, MarketLiquidity, MarketPriceStats, MarketSnapshot
from app.market_intelligence.analytics.outliers import remove_price_outliers
from app.market_intelligence.liquidity.liquidity_engine import LiquidityEngine
from app.market_intelligence.valuation.valuation_engine_v3 import quantile, round_money

class MarketJobs:
    def create_collection_job(self, db: Session, source: str, params: dict | None = None) -> MarketCollectionJob:
        job = MarketCollectionJob(source=source, status="queued", params=params or {})
        db.add(job); db.commit(); db.refresh(job)
        return job

    def rebuild_statistics(self, db: Session) -> dict:
        groups = db.query(MarketListing.brand, MarketListing.model, MarketListing.year, MarketListing.state).distinct().all()
        written = 0
        for brand, model, year, state in groups:
            rows = db.query(MarketListing).filter_by(brand=brand, model=model, year=year, state=state).all()
            prices = remove_price_outliers([float(r.price) for r in rows])
            if not prices: continue
            stats = MarketPriceStats(brand=brand, model=model, year=year, state=state, listing_count=len(prices), p25=round_money(quantile(prices,.25)), p50=round_money(quantile(prices,.5)), p75=round_money(quantile(prices,.75)), avg_price=round_money(sum(prices)/len(prices)), min_price=round_money(min(prices)), max_price=round_money(max(prices)))
            db.add(stats); written += 1
        db.commit(); return {"price_stats_written": written}

    def rebuild_liquidity(self, db: Session) -> dict:
        engine = LiquidityEngine(); written = 0
        groups = db.query(MarketListing.brand, MarketListing.model, MarketListing.year, MarketListing.state).distinct().all()
        for brand, model, year, state in groups:
            rows = db.query(MarketListing).filter_by(brand=brand, model=model, year=year, state=state).all()
            result = engine.calculate([float(r.price) for r in rows], regional_count=len(rows))
            db.add(MarketLiquidity(brand=brand, model=model, year=year, state=state, listing_count=result.listing_count, liquidity_score=result.score, liquidity_label=result.label, dispersion=result.dispersion, regional_volume=result.regional_volume))
            written += 1
        db.commit(); return {"liquidity_written": written}

    def create_snapshot(self, db: Session) -> dict:
        total = db.query(MarketListing).count()
        active = db.query(MarketListing).filter(getattr(MarketListing, "is_active", True) == True).count() if hasattr(MarketListing, "is_active") else total
        snap = MarketSnapshot(snapshot_at=datetime.now(timezone.utc), total_listings=total, active_listings=active, payload={"generated_by":"market_jobs"})
        db.add(snap); db.commit(); return {"snapshot_id": snap.id, "total_listings": total, "active_listings": active}
