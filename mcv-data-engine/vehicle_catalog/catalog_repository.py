from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from sqlalchemy import select
from storage.models import VehicleBrand, VehicleModelMaster, VehicleVersion, VehicleCatalogSyncRun
from .catalog_normalizer import canonical_brand, canonical_model, canonical_version, normalize_text

@dataclass
class CatalogUpsertStats:
    new_brands: int = 0
    new_models: int = 0
    new_versions: int = 0
    updated_brands: int = 0
    updated_models: int = 0
    updated_versions: int = 0
    skipped_existing: int = 0
    failed_items: int = 0
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return self.__dict__.copy()


class CatalogRepository:
    def __init__(self, session):
        self.session = session

    def start_run(self, run_type: str, vehicle_type: str | None = None) -> VehicleCatalogSyncRun:
        run = VehicleCatalogSyncRun(run_type=run_type, vehicle_type=vehicle_type, status="running", started_at=datetime.utcnow())
        self.session.add(run)
        self.session.commit()
        return run

    def finish_run(self, run: VehicleCatalogSyncRun, status: str, stats: CatalogUpsertStats, totals: dict | None = None, error_message: str | None = None) -> None:
        totals = totals or {}
        run.status = status
        run.total_brands_found = int(totals.get("brands", 0))
        run.total_models_found = int(totals.get("models", 0))
        run.total_versions_found = int(totals.get("versions", 0))
        run.new_brands = stats.new_brands
        run.new_models = stats.new_models
        run.new_versions = stats.new_versions
        run.updated_brands = stats.updated_brands
        run.updated_models = stats.updated_models
        run.updated_versions = stats.updated_versions
        run.skipped_existing = stats.skipped_existing
        run.failed_items = stats.failed_items
        run.error_message = error_message or "; ".join(stats.errors[:10]) or None
        run.finished_at = datetime.utcnow()
        self.session.commit()

    def upsert_brand(self, vehicle_type: str, fipe_brand_code: str | int, name: str, stats: CatalogUpsertStats | None = None) -> VehicleBrand:
        stats = stats or CatalogUpsertStats()
        code = str(fipe_brand_code)
        item = self.session.scalar(select(VehicleBrand).where(VehicleBrand.vehicle_type == vehicle_type, VehicleBrand.fipe_brand_code == code))
        now = datetime.utcnow()
        canonical = canonical_brand(name)
        normalized = normalize_text(canonical)
        if item:
            changed = item.canonical_name != canonical or item.normalized_name != normalized or not item.is_active
            item.canonical_name = canonical
            item.normalized_name = normalized
            item.is_active = True
            item.last_seen_at = now
            item.updated_at = now
            stats.updated_brands += int(changed)
            stats.skipped_existing += int(not changed)
        else:
            item = VehicleBrand(vehicle_type=vehicle_type, fipe_brand_code=code, canonical_name=canonical, normalized_name=normalized, source="FIPE", first_seen_at=now, last_seen_at=now, created_at=now, updated_at=now)
            self.session.add(item)
            self.session.flush()
            stats.new_brands += 1
        return item

    def upsert_model(self, brand: VehicleBrand, fipe_model_code: str | int, name: str, stats: CatalogUpsertStats | None = None) -> VehicleModelMaster:
        stats = stats or CatalogUpsertStats()
        code = str(fipe_model_code)
        item = self.session.scalar(select(VehicleModelMaster).where(VehicleModelMaster.vehicle_type == brand.vehicle_type, VehicleModelMaster.brand_id == brand.id, VehicleModelMaster.fipe_model_code == code))
        now = datetime.utcnow()
        canonical = canonical_model(name)
        normalized = normalize_text(canonical)
        if item:
            changed = item.canonical_name != canonical or item.normalized_name != normalized or not item.is_active
            item.canonical_name = canonical
            item.normalized_name = normalized
            item.is_active = True
            item.last_seen_at = now
            item.updated_at = now
            stats.updated_models += int(changed)
            stats.skipped_existing += int(not changed)
        else:
            item = VehicleModelMaster(brand_id=brand.id, vehicle_type=brand.vehicle_type, fipe_model_code=code, canonical_name=canonical, normalized_name=normalized, source="FIPE", first_seen_at=now, last_seen_at=now, created_at=now, updated_at=now)
            self.session.add(item)
            self.session.flush()
            stats.new_models += 1
        return item

    def upsert_version(self, brand: VehicleBrand, model: VehicleModelMaster, payload: dict, stats: CatalogUpsertStats | None = None) -> VehicleVersion:
        stats = stats or CatalogUpsertStats()
        year_code = str(payload.get("fipe_year_code") or payload.get("codigo_ano") or payload.get("codigo") or "")
        fipe_code = str(payload.get("fipe_code") or payload.get("codigo_fipe") or "")
        item = self.session.scalar(select(VehicleVersion).where(VehicleVersion.vehicle_type == brand.vehicle_type, VehicleVersion.model_id == model.id, VehicleVersion.fipe_year_code == year_code, VehicleVersion.fipe_code == fipe_code))
        now = datetime.utcnow()
        version_name = payload.get("version_name") or payload.get("modelo") or model.canonical_name
        normalized_version = normalize_text(canonical_version(version_name))
        fields = {
            "brand_id": brand.id, "model_id": model.id, "vehicle_type": brand.vehicle_type, "fipe_year_code": year_code,
            "fipe_code": fipe_code or None, "year": payload.get("year") or payload.get("ano"), "fuel": payload.get("fuel") or payload.get("combustivel"),
            "version_name": version_name, "normalized_version_name": normalized_version, "reference_month": payload.get("reference_month") or payload.get("mes_referencia"),
            "fipe_price": payload.get("fipe_price") or payload.get("preco_fipe") or payload.get("preco"), "source": "FIPE", "is_active": True,
        }
        if item:
            changed = False
            for k, v in fields.items():
                if getattr(item, k) != v:
                    setattr(item, k, v); changed = True
            item.last_seen_at = now
            item.updated_at = now
            stats.updated_versions += int(changed)
            stats.skipped_existing += int(not changed)
        else:
            item = VehicleVersion(**fields, first_seen_at=now, last_seen_at=now, created_at=now, updated_at=now)
            self.session.add(item)
            self.session.flush()
            stats.new_versions += 1
        return item


    def get_brand(self, vehicle_type: str, fipe_brand_code: str | int) -> VehicleBrand | None:
        code = str(fipe_brand_code)
        return self.session.scalar(select(VehicleBrand).where(VehicleBrand.vehicle_type == vehicle_type, VehicleBrand.fipe_brand_code == code))

    def get_model(self, brand_id: int, fipe_model_code: str | int) -> VehicleModelMaster | None:
        code = str(fipe_model_code)
        return self.session.scalar(select(VehicleModelMaster).where(VehicleModelMaster.brand_id == brand_id, VehicleModelMaster.fipe_model_code == code))

    def commit(self) -> None:
        self.session.commit()
