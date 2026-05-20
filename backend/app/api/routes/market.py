from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.api.deps import current_user
from app.db.session import get_db
from app.market_sources.csv_import import parse_market_csv
from app.market_intelligence.pipelines.market_pipeline import MarketIngestionPipeline
from app.market_intelligence.jobs.market_jobs import MarketJobs
from app.market_intelligence.schedulers.scheduler import SCHEDULED_JOBS
from app.models.market import MarketCollectionJob, MarketListing, MarketLiquidity, MarketPriceStats, MarketSnapshot
from app.models.user import User

router = APIRouter(prefix="/market", tags=["market"])


@router.post("/import-csv")
async def import_market_csv(file: UploadFile = File(...), db: Session = Depends(get_db), user: User = Depends(current_user)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Envie um arquivo CSV.")
    content = await file.read()
    rows, errors = parse_market_csv(content)
    pipeline_rows = [row.__dict__ for row in rows]
    summary = MarketIngestionPipeline().ingest_rows(db, pipeline_rows, source="csv")
    return {"imported": summary["imported"], "ignored": len(errors) + summary["suspicious"] + summary["errors"], "duplicates": summary["duplicates"], "total_rows": len(rows) + len(errors), "errors": errors[:30]}


@router.get("/listings")
def list_market_listings(db: Session = Depends(get_db), user: User = Depends(current_user), limit: int = 50):
    rows = db.query(MarketListing).order_by(MarketListing.collected_at.desc()).limit(min(limit, 200)).all()
    return [{"id": row.id, "title": row.title, "price": row.price, "brand": row.brand, "model": row.model, "version": row.version, "year": row.year, "mileage": row.mileage, "city": row.city, "state": row.state, "source": row.source, "duplicate_score": getattr(row, "duplicate_score", 0), "collected_at": str(row.collected_at)} for row in rows]


@router.get("/admin/overview")
def admin_market_overview(db: Session = Depends(get_db), user: User = Depends(current_user)):
    total = db.query(MarketListing).count()
    valid = db.query(MarketListing).filter(MarketListing.price > 5000, MarketListing.year >= 1970).count()
    duplicate_count = db.query(MarketListing).filter(MarketListing.duplicate_score >= 65).count()
    sources = db.query(MarketListing.source, func.count(MarketListing.id)).group_by(MarketListing.source).all()
    states = db.query(MarketListing.state, func.count(MarketListing.id)).group_by(MarketListing.state).order_by(func.count(MarketListing.id).desc()).limit(10).all()
    latest_jobs = db.query(MarketCollectionJob).order_by(MarketCollectionJob.created_at.desc()).limit(8).all()
    latest_snapshot = db.query(MarketSnapshot).order_by(MarketSnapshot.snapshot_at.desc()).first()
    return {"total_listings": total, "valid_listings": valid, "duplicates_detected": duplicate_count, "active_sources": [{"source": s, "count": c} for s, c in sources], "top_regions": [{"state": s or "--", "count": c} for s, c in states], "scheduled_jobs": SCHEDULED_JOBS, "latest_jobs": [{"id": j.id, "source": j.source, "status": j.status, "imported": j.imported_count, "duplicates": j.duplicate_count, "errors": j.error_count, "created_at": str(j.created_at)} for j in latest_jobs], "latest_snapshot": {"id": latest_snapshot.id, "snapshot_at": str(latest_snapshot.snapshot_at), "total_listings": latest_snapshot.total_listings, "active_listings": latest_snapshot.active_listings} if latest_snapshot else None}


@router.post("/admin/rebuild-statistics")
def rebuild_statistics(db: Session = Depends(get_db), user: User = Depends(current_user)):
    jobs = MarketJobs()
    return {**jobs.rebuild_statistics(db), **jobs.rebuild_liquidity(db), **jobs.create_snapshot(db)}


@router.post("/admin/jobs")
def create_collection_job(source: str, db: Session = Depends(get_db), user: User = Depends(current_user)):
    job = MarketJobs().create_collection_job(db, source=source, params={"created_from":"admin"})
    return {"id": job.id, "source": job.source, "status": job.status, "message": "Job criado. Coletores externos permanecem desabilitados até validação de API/ToS/robots."}

from app.core.config import settings as _settings
from app.data_engine_bridge import DataEngineExportLoader


@router.get("/data-engine/status")
def data_engine_status(user: User = Depends(current_user)):
    loader = DataEngineExportLoader(_settings.data_engine_exports_path)
    validation = loader.validate_exports()
    return {
        "exports_path": str(loader.exports_path),
        "available": validation.available,
        "validation_status": validation.status,
        "errors": validation.errors,
        "manifest": validation.manifest,
        "files": validation.files,
    }


@router.get("/data-engine/manifest")
def data_engine_manifest(user: User = Depends(current_user)):
    loader = DataEngineExportLoader(_settings.data_engine_exports_path)
    return loader.load_manifest()
