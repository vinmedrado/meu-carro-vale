from app.vehicle_catalog.models import VehicleCatalogSyncJob
from app.vehicle_catalog.normalizers.catalog_normalizer import normalize_brand_name
from app.vehicle_catalog.services.catalog_service import VehicleCatalogService
from app.vehicle_catalog.services.fipe_catalog_sync import FipeCatalogSyncService

class FakeFipePartial:
    def brands(self, vehicle_type="carros"):
        return [{"code": "59", "name": "Chevrolet"}]
    def models(self, vehicle_type, brand_code):
        return [{"code": "10", "name": "Tracker Premier 1.2 Turbo"}]
    def years(self, vehicle_type, brand_code, model_code):
        return [{"code": "2023-1", "name": "2023 Gasolina"}]
    def price(self, db, vehicle_type, brand_code, model_code, year_code):
        return {"vehicle_type": vehicle_type, "brand": "chevrolet", "model": "tracker", "year": 2023, "fipe_code": "004999-0", "fuel": "Gasolina", "reference_month": "maio de 2026", "value": 120000.0}

class FakeFipeError(FakeFipePartial):
    def models(self, vehicle_type, brand_code):
        raise RuntimeError("FIPE indisponível")


def seed_aliases(db_session):
    service = VehicleCatalogService()
    service.ensure_manual_alias_catalog(db_session)
    return service


def test_requested_brand_aliases():
    assert normalize_brand_name("GM") == "chevrolet"
    assert normalize_brand_name("General Motors") == "chevrolet"
    assert normalize_brand_name("VW") == "volkswagen"
    assert normalize_brand_name("Wolkswagen") == "volkswagen"
    assert normalize_brand_name("Mercedes Benz") == "mercedes-benz"


def test_requested_model_aliases(db_session):
    service = seed_aliases(db_session)
    cases = [
        ("GM", "Corsa Classic", "chevrolet", "corsa"),
        ("General Motors", "Prisma", "chevrolet", "onix plus"),
        ("VW", "TCross", "volkswagen", "t-cross"),
        ("Honda", "HRV", "honda", "hr-v"),
        ("GM", "S-10", "chevrolet", "s10"),
        ("Toyota", "Hilux SW4", "toyota", "sw4"),
    ]
    for brand, text, expected_brand, expected_model in cases:
        result = service.normalize_vehicle_text(db_session, text, brand_hint=brand)
        assert result.canonical_brand == expected_brand
        assert result.canonical_model == expected_model
        assert result.confidence_score >= 80


def test_catalog_sync_job_progress_and_partial_success(db_session):
    service = FipeCatalogSyncService(fipe=FakeFipePartial())
    job = service.create_job(db_session, vehicle_type="carros")
    result = service.sync_job(db_session, job.id, vehicle_types=["carros"])
    db_session.refresh(job)
    assert result.status == "success"
    assert job.status == "completed"
    assert job.processed_brands == 1
    assert job.processed_models == 1
    assert job.processed_versions == 1


def test_catalog_sync_fallback_on_fipe_error(db_session):
    service = FipeCatalogSyncService(fipe=FakeFipeError())
    job = service.create_job(db_session, vehicle_type="carros")
    result = service.sync_job(db_session, job.id, vehicle_types=["carros"])
    db_session.refresh(job)
    assert result.status == "partial_success"
    assert job.status == "partial_success"
    assert "FIPE indisponível" in job.error_message
