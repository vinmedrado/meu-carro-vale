from __future__ import annotations
from app.db.session import SessionLocal
from app.vehicle_catalog.services.fipe_catalog_sync import FipeCatalogSyncService

def run(vehicle_types=None, limit_brands=None, limit_models=None):
    db = SessionLocal()
    try:
        job = FipeCatalogSyncService().create_job(db, vehicle_type=",".join(vehicle_types) if vehicle_types else None)
        return FipeCatalogSyncService().sync_job(db, job.id, vehicle_types=vehicle_types, limit_brands=limit_brands, limit_models=limit_models)
    finally:
        db.close()

if __name__ == "__main__":
    print(run().__dict__)
