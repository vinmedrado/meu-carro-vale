from __future__ import annotations
import json
from pathlib import Path

from sqlalchemy import create_engine, select
from storage.models import Base, get_session_factory, VehicleBrand, VehicleModelMaster, VehicleVersion
from vehicle_catalog.catalog_repository import CatalogRepository, CatalogUpsertStats
from vehicle_catalog.catalog_normalizer import canonical_brand, normalize_text
from vehicle_catalog.catalog_search_index import CatalogSearchIndexBuilder


def make_session():
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    return get_session_factory(engine)()


def seed_catalog(session):
    repo = CatalogRepository(session)
    stats = CatalogUpsertStats()
    brand = repo.upsert_brand("carros", "23", "GM", stats)
    model = repo.upsert_model(brand, "1001", "Agile", stats)
    repo.upsert_version(brand, model, {"fipe_year_code": "2013-1", "fipe_code": "004381-1", "year": 2013, "fuel": "Flex", "version_name": "Agile LTZ 1.4 Flex", "reference_month": "maio/2026", "fipe_price": 38900.0}, stats)
    repo.commit()
    return stats


def test_alias_gm_converge_para_chevrolet():
    assert canonical_brand("GM") == "Chevrolet"
    assert normalize_text(canonical_brand("General Motors")) == "chevrolet"


def test_catalog_upsert_incremental_nao_duplica():
    session = make_session()
    stats1 = seed_catalog(session)
    stats2 = seed_catalog(session)
    assert stats1.new_brands == 1
    assert session.scalar(select(VehicleBrand).where(VehicleBrand.vehicle_type == "carros")).canonical_name == "Chevrolet"
    assert len(session.scalars(select(VehicleBrand)).all()) == 1
    assert len(session.scalars(select(VehicleModelMaster)).all()) == 1
    assert len(session.scalars(select(VehicleVersion)).all()) == 1
    assert stats2.skipped_existing >= 1


def test_preco_fipe_atualiza_sem_criar_nova_versao():
    session = make_session()
    seed_catalog(session)
    repo = CatalogRepository(session)
    stats = CatalogUpsertStats()
    brand = session.scalar(select(VehicleBrand))
    model = session.scalar(select(VehicleModelMaster))
    repo.upsert_version(brand, model, {"fipe_year_code": "2013-1", "fipe_code": "004381-1", "year": 2013, "fuel": "Flex", "version_name": "Agile LTZ 1.4 Flex", "reference_month": "junho/2026", "fipe_price": 39750.0}, stats)
    repo.commit()
    versions = session.scalars(select(VehicleVersion)).all()
    assert len(versions) == 1
    assert versions[0].fipe_price == 39750.0
    assert versions[0].reference_month == "junho/2026"


def test_busca_agile_com_alias(tmp_path, monkeypatch):
    session = make_session()
    seed_catalog(session)
    # Reaponta temporariamente init_db/session do módulo de índice para este banco em memória.
    import vehicle_catalog.catalog_search_index as search_module
    monkeypatch.setattr(search_module, "init_db", lambda: session.get_bind())
    monkeypatch.setattr(search_module, "get_session_factory", lambda engine: lambda: session)
    results = CatalogSearchIndexBuilder(tmp_path).search("Agile LTZ 2013")
    assert results
    assert results[0]["marca"] == "Chevrolet"
    assert "Agile" in results[0]["modelo"]
