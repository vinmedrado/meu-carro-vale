from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Thread
from typing import Iterable
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.fipe_service import FipeService, VEHICLE_TYPES
from app.vehicle_catalog.models import VehicleCatalogSyncJob, VehicleCatalogSyncLog
from app.vehicle_catalog.normalizers.catalog_normalizer import normalize_fuel, parse_year
from app.vehicle_catalog.services.catalog_service import VehicleCatalogService

@dataclass
class SyncSummary:
    status: str
    vehicle_types: list[str]
    brands: int = 0
    models: int = 0
    versions: int = 0
    errors: list[str] | None = None
    job_id: int | None = None

class FipeCatalogSyncService:
    def __init__(self, fipe: FipeService | None = None, catalog: VehicleCatalogService | None = None):
        self.fipe = fipe or FipeService()
        self.catalog = catalog or VehicleCatalogService()

    def create_job(self, db: Session, vehicle_type: str | None = None) -> VehicleCatalogSyncJob:
        vt = vehicle_type or "all"
        job = VehicleCatalogSyncJob(status="pending", vehicle_type=vt)
        db.add(job); db.commit(); db.refresh(job)
        return job

    def start_background_job(self, db: Session, vehicle_type: str | None = None, limit_brands: int | None = None, limit_models: int | None = None) -> VehicleCatalogSyncJob:
        job = self.create_job(db, vehicle_type)
        thread = Thread(target=run_catalog_sync_job, args=(job.id, vehicle_type, limit_brands, limit_models), daemon=True)
        thread.start()
        return job

    def sync_job(self, db: Session, job_id: int, vehicle_types: Iterable[str] | None = None, limit_brands: int | None = None, limit_models: int | None = None) -> SyncSummary:
        job = db.get(VehicleCatalogSyncJob, job_id)
        if not job:
            raise ValueError("job não encontrado")
        job.status = "running"; job.started_at = datetime.now(timezone.utc); job.error_message = ""; db.commit()
        summary = self.sync(db, vehicle_types=vehicle_types, limit_brands=limit_brands, limit_models=limit_models, job=job)
        return summary

    def sync(self, db: Session, vehicle_types: Iterable[str] | None = None, limit_brands: int | None = None, limit_models: int | None = None, job: VehicleCatalogSyncJob | None = None) -> SyncSummary:
        types = [v for v in (vehicle_types or VEHICLE_TYPES) if v in VEHICLE_TYPES]
        summary = SyncSummary(status="success", vehicle_types=types, errors=[], job_id=job.id if job else None)
        log = VehicleCatalogSyncLog(status="running", vehicle_type=",".join(types))
        db.add(log); db.commit(); db.refresh(log)
        try:
            for vehicle_type in types:
                brands = self.fipe.brands(vehicle_type)
                selected_brands = brands[:limit_brands or len(brands)]
                if job:
                    job.vehicle_type = vehicle_type if len(types) == 1 else "all"
                    job.total_brands += len(selected_brands)
                    db.commit()
                for brand_data in selected_brands:
                    brand = self.catalog.ensure_brand(db, vehicle_type, brand_data["code"], brand_data["name"]); summary.brands += 1
                    try:
                        models = self.fipe.models(vehicle_type, brand.fipe_code)
                    except Exception as exc:
                        summary.errors.append(f"modelos {brand.canonical_name}: {exc}"); models = []
                    selected_models = models[:limit_models or len(models)]
                    if job:
                        job.processed_brands += 1; job.total_models += len(selected_models); db.commit()
                    for model_data in selected_models:
                        model = self.catalog.ensure_model(db, brand, model_data["code"], model_data["name"]); summary.models += 1
                        try:
                            years = self.fipe.years(vehicle_type, brand.fipe_code, model.fipe_code)
                        except Exception as exc:
                            summary.errors.append(f"anos {brand.canonical_name}/{model.canonical_name}: {exc}"); years = []
                        if job:
                            job.processed_models += 1; job.total_versions += len(years); db.commit()
                        for year_data in years:
                            try:
                                price = self.fipe.price(db, vehicle_type, brand.fipe_code, model.fipe_code, year_data["code"])
                                self.catalog.ensure_version(db, model, year_data["code"], parse_year(price.get("year") or year_data.get("name")), normalize_fuel(price.get("fuel")), price.get("model") or model.canonical_name, price.get("fipe_code") or "", price.get("reference_month") or "", float(price.get("value") or 0))
                                summary.versions += 1
                            except Exception as exc:
                                summary.errors.append(f"preço {brand.canonical_name}/{model.canonical_name}/{year_data.get('code')}: {exc}")
                            finally:
                                if job:
                                    job.processed_versions += 1; db.commit()
                    db.commit()
            final_status = "success" if not summary.errors else "partial_success"
            log.status = final_status
            if job:
                job.status = "completed" if final_status == "success" else "partial_success"
        except Exception as exc:
            summary.status = "failed"; summary.errors.append(str(exc)); log.status = "failed"; log.error_message = str(exc)
            if job:
                job.status = "failed"; job.error_message = str(exc)
        log.brands_count = summary.brands; log.models_count = summary.models; log.versions_count = summary.versions
        if summary.errors and not log.error_message: log.error_message = " | ".join(summary.errors[:10])
        if job:
            job.finished_at = datetime.now(timezone.utc)
            if summary.errors and not job.error_message: job.error_message = " | ".join(summary.errors[:10])
        db.commit()
        summary.status = log.status
        return summary


def run_catalog_sync_job(job_id: int, vehicle_type: str | None = None, limit_brands: int | None = None, limit_models: int | None = None) -> None:
    db = SessionLocal()
    try:
        types = [vehicle_type] if vehicle_type else None
        FipeCatalogSyncService().sync_job(db, job_id, vehicle_types=types, limit_brands=limit_brands, limit_models=limit_models)
    except Exception as exc:
        job = db.get(VehicleCatalogSyncJob, job_id)
        if job:
            job.status = "failed"; job.error_message = str(exc); job.finished_at = datetime.now(timezone.utc); db.commit()
    finally:
        db.close()
