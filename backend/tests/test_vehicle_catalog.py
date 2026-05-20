from app.db.session import Base
from app.vehicle_catalog.normalizers.catalog_normalizer import normalize_brand_name, normalize_model_name
from app.vehicle_catalog.services.catalog_service import VehicleCatalogService
from app.vehicle_catalog.services.fipe_catalog_sync import FipeCatalogSyncService


class FakeFipe:
    def brands(self, vehicle_type="carros"):
        return [{"code": "59", "name": "Chevrolet"}]

    def models(self, vehicle_type, brand_code):
        return [{"code": "1", "name": "ONIX HATCH 1.0 Flex"}]

    def years(self, vehicle_type, brand_code, model_code):
        return [{"code": "2021-1", "name": "2021 Gasolina"}]

    def price(self, db, vehicle_type, brand_code, model_code, year_code):
        return {"vehicle_type": vehicle_type, "brand": "chevrolet", "model": "onix", "year": 2021, "fipe_code": "004001-0", "fuel": "Gasolina", "reference_month": "maio de 2026", "value": 65000.0}


def test_brand_alias_normalization():
    assert normalize_brand_name("GM") == "chevrolet"
    assert normalize_brand_name("General Motors") == "chevrolet"
    assert normalize_brand_name("VW") == "volkswagen"
    assert normalize_brand_name("Toyta") == "toyota"
    assert normalize_brand_name("Hoda") == "honda"


def test_model_normalization_removes_noise():
    assert normalize_model_name("ONIX HATCH 1.0 Flex") == "onix 1 0"


def test_catalog_sync_deduplicates_and_searches(db_session):
    sync = FipeCatalogSyncService(fipe=FakeFipe())
    first = sync.sync(db_session, vehicle_types=["carros"])
    second = sync.sync(db_session, vehicle_types=["carros"])
    service = VehicleCatalogService()
    found = service.search(db_session, "gm")
    brand = service.resolve_brand(db_session, "General Motors")
    model = service.resolve_model(db_session, brand.id, "Onix")
    versions = service.list_versions(db_session, model.id)
    assert first.status == "success"
    assert second.status == "success"
    assert len(service.list_brands(db_session, "carros")) == 1
    assert found["brands"][0].canonical_name == "chevrolet"
    assert versions[0].fipe_code == "004001-0"
