from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.api.deps import current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.vehicle_catalog.models import VehicleBrand, VehicleCatalogSyncJob, VehicleCatalogSyncLog, VehicleModel, VehicleVersion
from app.vehicle_catalog.services.catalog_service import VehicleCatalogService
from app.vehicle_catalog.services.fipe_catalog_sync import FipeCatalogSyncService

router = APIRouter(prefix="/catalog", tags=["catalog"])
service = VehicleCatalogService()


def brand_out(row: VehicleBrand):
    return {"id": row.id, "vehicle_type": row.vehicle_type, "canonical_name": row.canonical_name, "fipe_code": row.fipe_code, "is_active": row.is_active}

def model_out(row: VehicleModel):
    return {"id": row.id, "brand_id": row.brand_id, "canonical_name": row.canonical_name, "fipe_code": row.fipe_code, "is_active": row.is_active}

def version_out(row: VehicleVersion):
    return {"id": row.id, "model_id": row.model_id, "fipe_year_code": row.fipe_year_code, "year": row.year, "fuel": row.fuel, "version_name": row.version_name, "fipe_code": row.fipe_code, "reference_month": row.reference_month, "fipe_price": row.fipe_price}

def job_out(job: VehicleCatalogSyncJob):
    total = job.total_brands + job.total_models + job.total_versions
    done = job.processed_brands + job.processed_models + job.processed_versions
    progress = round((done / total) * 100, 2) if total else (100 if job.status in {"completed", "partial_success"} else 0)
    return {
        "id": job.id,
        "status": job.status,
        "vehicle_type": job.vehicle_type,
        "total_brands": job.total_brands,
        "processed_brands": job.processed_brands,
        "total_models": job.total_models,
        "processed_models": job.processed_models,
        "total_versions": job.total_versions,
        "processed_versions": job.processed_versions,
        "progress_percent": progress,
        "started_at": str(job.started_at) if job.started_at else None,
        "finished_at": str(job.finished_at) if job.finished_at else None,
        "error_message": job.error_message,
        "created_at": str(job.created_at) if job.created_at else None,
        "updated_at": str(job.updated_at) if job.updated_at else None,
    }

@router.get("/brands")
def list_brands(vehicle_type: str | None = None, db: Session = Depends(get_db)):
    return [brand_out(row) for row in service.list_brands(db, vehicle_type)]

@router.get("/models")
def list_models(brand_id: int = Query(...), db: Session = Depends(get_db)):
    return [model_out(row) for row in service.list_models(db, brand_id)]

@router.get("/versions")
def list_versions(model_id: int = Query(...), db: Session = Depends(get_db)):
    return [version_out(row) for row in service.list_versions(db, model_id)]

@router.get("/search")
def search_catalog(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    result = service.search(db, q)
    return {"brands": [brand_out(row) for row in result["brands"]], "models": [model_out(row) for row in result["models"]]}

@router.get("/normalize")
def normalize_catalog_text(q: str = Query(..., min_length=1), brand: str | None = None, db: Session = Depends(get_db)):
    result = service.normalize_vehicle_text(db, q, brand_hint=brand)
    return result.__dict__

@router.post("/sync-fipe")
def sync_fipe_catalog(vehicle_type: str | None = None, limit_brands: int | None = None, limit_models: int | None = None, db: Session = Depends(get_db), user: User = Depends(current_user)):
    if vehicle_type and vehicle_type not in {"carros", "motos", "caminhoes"}:
        raise HTTPException(status_code=422, detail="vehicle_type deve ser carros, motos ou caminhoes")
    if settings.app_mode.upper() == "DEMO":
        limit_brands = limit_brands or 5
        limit_models = limit_models or 8
    job = FipeCatalogSyncService().start_background_job(db, vehicle_type=vehicle_type, limit_brands=limit_brands, limit_models=limit_models)
    return {"message": "Sincronização FIPE iniciada em background", "job": job_out(job)}

@router.get("/sync-status/{job_id}")
def sync_status(job_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    job = db.get(VehicleCatalogSyncJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job não encontrado")
    return job_out(job)

@router.get("/sync-jobs")
def sync_jobs(limit: int = 20, db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.query(VehicleCatalogSyncJob).order_by(VehicleCatalogSyncJob.created_at.desc()).limit(limit).all()
    return [job_out(row) for row in rows]

@router.post("/seed-aliases")
def seed_aliases(db: Session = Depends(get_db), user: User = Depends(current_user)):
    service.ensure_manual_alias_catalog(db)
    return {"status": "ok", "message": "Aliases brasileiros de marcas e modelos garantidos."}

@router.get("/admin/overview")
def catalog_admin_overview(db: Session = Depends(get_db), user: User = Depends(current_user)):
    latest_job = db.query(VehicleCatalogSyncJob).order_by(VehicleCatalogSyncJob.created_at.desc()).first()
    latest_log = db.query(VehicleCatalogSyncLog).order_by(VehicleCatalogSyncLog.created_at.desc()).first()
    recent_errors = db.query(VehicleCatalogSyncJob).filter(VehicleCatalogSyncJob.error_message != "").order_by(VehicleCatalogSyncJob.created_at.desc()).limit(5).all()
    by_type = db.query(VehicleBrand.vehicle_type, func.count(VehicleBrand.id)).group_by(VehicleBrand.vehicle_type).all()
    return {
        "total_brands": db.query(VehicleBrand).count(),
        "total_models": db.query(VehicleModel).count(),
        "total_versions": db.query(VehicleVersion).count(),
        "brands_by_type": [{"vehicle_type": t, "count": c} for t, c in by_type],
        "latest_sync": job_out(latest_job) if latest_job else ({"id": latest_log.id, "status": latest_log.status, "vehicle_type": latest_log.vehicle_type, "created_at": str(latest_log.created_at), "error_message": latest_log.error_message} if latest_log else None),
        "recent_errors": [job_out(e) for e in recent_errors],
    }
