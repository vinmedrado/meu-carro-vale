from __future__ import annotations
import shutil
import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from fastapi import FastAPI, File, UploadFile, Query
from pydantic import BaseModel
from sqlalchemy import select

from jobs.pipeline import MCVDataPipeline
from comparables.comparable_intelligence_engine import ComparableIntelligenceEngine
from market_behavior.market_behavior_engine import MarketBehaviorEngine
from market_behavior.price_pressure_engine import PricePressureEngine
from market_behavior.market_velocity_engine import MarketVelocityEngine
from market_behavior.resistance_engine import ResistanceEngine
from market_behavior.regional_behavior_engine import RegionalBehaviorEngine
from market_behavior.trend_behavior_engine import TrendBehaviorEngine
from ingestion.validators.data_quality_engine import DataQualityEngine
from normalizers.vehicle_normalizer import VehicleNormalizer
from storage.models import MarketListing, MarketSnapshot, MarketLiquidity, MarketQuality, init_db, get_session_factory

from pipeline_orchestrator import PipelineOrchestrator
from validation.export_validation_engine import ExportValidationEngine

app = FastAPI(title="MCV Data Engine API", version="0.3.0")
engine = init_db()
SessionFactory = get_session_factory(engine)


class BatchPayload(BaseModel):
    records: list[dict[str, Any]]
    persist: bool = False


def _serialize(row):
    return {k: v for k, v in row.__dict__.items() if not k.startswith("_sa_")}


def _tmp_upload(upload: UploadFile, suffix: str) -> Path:
    tmp = NamedTemporaryFile(delete=False, suffix=suffix)
    with tmp as fh:
        shutil.copyfileobj(upload.file, fh)
    return Path(tmp.name)


@app.get("/health")
def health():
    return {"status": "ok", "service": "mcv-data-engine", "version": "0.3.0"}


@app.post("/ingestion/csv")
def ingest_csv(file: UploadFile = File(...), persist: bool = False):
    path = _tmp_upload(file, ".csv")
    try:
        return MCVDataPipeline().run_import(path, persist=persist)
    finally:
        path.unlink(missing_ok=True)


@app.post("/ingestion/json")
def ingest_json(file: UploadFile = File(...), persist: bool = False):
    path = _tmp_upload(file, ".json")
    try:
        return MCVDataPipeline().run_import(path, persist=persist)
    finally:
        path.unlink(missing_ok=True)


@app.post("/ingestion/batch")
def ingest_batch(payload: BatchPayload):
    return MCVDataPipeline().process_records(payload.records, persist=payload.persist)


@app.get("/market/listings")
def listings(marca: str | None = None, modelo: str | None = None, limit: int = Query(50, le=1000)):
    with SessionFactory() as session:
        stmt = select(MarketListing).limit(limit)
        if marca:
            stmt = stmt.where(MarketListing.marca == marca)
        if modelo:
            stmt = stmt.where(MarketListing.modelo == modelo)
        return [_serialize(row) for row in session.scalars(stmt).all()]


@app.get("/market/snapshots")
def snapshots(limit: int = Query(50, le=1000)):
    with SessionFactory() as session:
        return [_serialize(row) for row in session.scalars(select(MarketSnapshot).limit(limit)).all()]


@app.get("/market/liquidity")
def liquidity(limit: int = Query(50, le=1000)):
    with SessionFactory() as session:
        return [_serialize(row) for row in session.scalars(select(MarketLiquidity).limit(limit)).all()]


@app.get("/market/quality")
def quality(limit: int = Query(50, le=1000)):
    with SessionFactory() as session:
        return [_serialize(row) for row in session.scalars(select(MarketQuality).limit(limit)).all()]


@app.get("/market/comparables")
def comparables(
    brand: str | None = None,
    model: str | None = None,
    version: str | None = None,
    year: int | None = None,
    mileage: int | None = None,
    state: str | None = None,
    city: str | None = None,
    marca: str | None = None,
    modelo: str | None = None,
    versao: str | None = None,
    ano: int | None = None,
    km: int | None = None,
    estado: str | None = None,
    cidade: str | None = None,
    limit: int = Query(30, le=200),
):
    raw_target = {
        "marca": brand or marca,
        "modelo": model or modelo,
        "versao": version or versao,
        "ano": year or ano,
        "km": mileage or km,
        "estado": state or estado,
        "cidade": city or cidade,
        "preco": None,
        "fonte": "consulta_api",
    }
    normalizer = VehicleNormalizer()
    quality = DataQualityEngine()
    target = quality.enrich(normalizer.normalize(raw_target))
    with SessionFactory() as session:
        stmt = select(MarketListing).where(MarketListing.duplicado == False)  # noqa: E712
        if target.get("marca"):
            stmt = stmt.where(MarketListing.marca == target["marca"])
        if target.get("modelo"):
            stmt = stmt.where(MarketListing.modelo == target["modelo"])
        if target.get("ano"):
            stmt = stmt.where(MarketListing.ano.between(int(target["ano"]) - 2, int(target["ano"]) + 2))
        rows = [_serialize(row) for row in session.scalars(stmt.limit(1000)).all()]
    engine = ComparableIntelligenceEngine()
    result = engine.find_comparables(target, rows, limit=limit)
    return {
        "target": {k: target.get(k) for k in ["marca", "modelo", "versao", "ano", "km", "cidade", "estado"]},
        "comparables": result["comparables"],
        "sample_statistics": result["sample_statistics"],
        "outliers_removed": result["outliers_removed"],
    }



def _market_query_target(brand=None, model=None, version=None, year=None, mileage=None, state=None, city=None, marca=None, modelo=None, versao=None, ano=None, km=None, estado=None, cidade=None, preco=None):
    raw_target = {
        "marca": brand or marca,
        "modelo": model or modelo,
        "versao": version or versao,
        "ano": year or ano,
        "km": mileage or km,
        "estado": state or estado,
        "cidade": city or cidade,
        "preco": preco,
        "fonte": "consulta_api",
    }
    return DataQualityEngine().enrich(VehicleNormalizer().normalize(raw_target))


def _load_clean_comparables_and_snapshots(target: dict[str, Any], limit: int = 300):
    with SessionFactory() as session:
        stmt = select(MarketListing).where(MarketListing.duplicado == False)  # noqa: E712
        if target.get("marca"):
            stmt = stmt.where(MarketListing.marca == target["marca"])
        if target.get("modelo"):
            stmt = stmt.where(MarketListing.modelo == target["modelo"])
        if target.get("ano"):
            stmt = stmt.where(MarketListing.ano.between(int(target["ano"]) - 2, int(target["ano"]) + 2))
        listings = [_serialize(row) for row in session.scalars(stmt.limit(limit)).all()]
        snap_stmt = select(MarketSnapshot)
        if target.get("marca"):
            snap_stmt = snap_stmt.where(MarketSnapshot.marca == target["marca"])
        if target.get("modelo"):
            snap_stmt = snap_stmt.where(MarketSnapshot.modelo == target["modelo"])
        if target.get("ano"):
            snap_stmt = snap_stmt.where(MarketSnapshot.ano.between(int(target["ano"]) - 2, int(target["ano"]) + 2))
        snapshots = [_serialize(row) for row in session.scalars(snap_stmt.limit(200)).all()]
    comparable_result = ComparableIntelligenceEngine(min_score=50).find_comparables(target, listings, limit=limit)
    return comparable_result["comparables"], snapshots, comparable_result.get("sample_statistics", {})


def _behavior_params(brand=None, model=None, version=None, year=None, mileage=None, state=None, city=None, marca=None, modelo=None, versao=None, ano=None, km=None, estado=None, cidade=None, preco=None, limit: int = 300):
    target = _market_query_target(brand, model, version, year, mileage, state, city, marca, modelo, versao, ano, km, estado, cidade, preco)
    comparables, snapshots, stats = _load_clean_comparables_and_snapshots(target, limit=limit)
    return target, comparables, snapshots, stats


@app.get("/market/behavior")
def market_behavior(
    brand: str | None = None, model: str | None = None, version: str | None = None, year: int | None = None,
    mileage: int | None = None, state: str | None = None, city: str | None = None, preco: float | None = None,
    marca: str | None = None, modelo: str | None = None, versao: str | None = None, ano: int | None = None,
    km: int | None = None, estado: str | None = None, cidade: str | None = None, limit: int = Query(300, le=1000),
):
    target, comps, snaps, stats = _behavior_params(brand, model, version, year, mileage, state, city, marca, modelo, versao, ano, km, estado, cidade, preco, limit)
    behavior = MarketBehaviorEngine().analyze(comps, snaps, target)
    return {"target": target, "sample_statistics": stats, "behavior": behavior}


@app.get("/market/price-pressure")
def market_price_pressure(brand: str | None = None, model: str | None = None, year: int | None = None, state: str | None = None, city: str | None = None, preco: float | None = None, limit: int = Query(300, le=1000)):
    target, comps, _, _ = _behavior_params(brand=brand, model=model, year=year, state=state, city=city, preco=preco, limit=limit)
    return {"target": target, "price_pressure": PricePressureEngine().analyze(comps, target_price=target.get("preco"))}


@app.get("/market/velocity")
def market_velocity(brand: str | None = None, model: str | None = None, year: int | None = None, state: str | None = None, city: str | None = None, limit: int = Query(300, le=1000)):
    target, comps, snaps, _ = _behavior_params(brand=brand, model=model, year=year, state=state, city=city, limit=limit)
    return {"target": target, "velocity": MarketVelocityEngine().analyze(comps, snaps)}


@app.get("/market/resistance")
def market_resistance(brand: str | None = None, model: str | None = None, year: int | None = None, state: str | None = None, city: str | None = None, preco: float | None = None, limit: int = Query(300, le=1000)):
    target, comps, snaps, _ = _behavior_params(brand=brand, model=model, year=year, state=state, city=city, preco=preco, limit=limit)
    pressure = PricePressureEngine().analyze(comps, target.get("preco"))
    velocity = MarketVelocityEngine().analyze(comps, snaps)
    return {"target": target, "resistance": ResistanceEngine().analyze(comps, target.get("preco"), pressure.get("price_pressure_score", 0), velocity.get("market_velocity_score", 0))}


@app.get("/market/regional-behavior")
def market_regional_behavior(brand: str | None = None, model: str | None = None, year: int | None = None, state: str | None = None, city: str | None = None, limit: int = Query(300, le=1000)):
    target, comps, _, _ = _behavior_params(brand=brand, model=model, year=year, state=state, city=city, limit=limit)
    return {"target": target, "regional_behavior": RegionalBehaviorEngine().analyze(comps, target.get("estado"), target.get("cidade"))}


@app.get("/market/trends")
def market_trends(brand: str | None = None, model: str | None = None, year: int | None = None, state: str | None = None, city: str | None = None, limit: int = Query(300, le=1000)):
    target, _, snaps, _ = _behavior_params(brand=brand, model=model, year=year, state=state, city=city, limit=limit)
    return {"target": target, "trends": TrendBehaviorEngine().analyze(snaps)}


@app.post("/ops/pipeline/run")
def run_pipeline(input_path: str = "sample_market_listings.csv", only: str | None = None, persist: bool = False):
    """Executa o pipeline operacional do data engine com suporte a execução parcial."""
    return PipelineOrchestrator().run(input_path=input_path, only=only, persist=persist)


@app.get("/ops/exports/validate")
def validate_exports():
    """Valida contratos oficiais dos exports consumidos pelo Meu Carro Vale."""
    return ExportValidationEngine().validate_all(["comparables", "liquidity", "market_behavior", "snapshots", "normalized_catalog"])


@app.get("/ops/exports/manifest")
def export_manifest():
    """Gera e retorna o manifesto operacional dos exports."""
    validator = ExportValidationEngine()
    return validator.write_manifest(validator.validate_all(["comparables", "liquidity", "market_behavior", "snapshots", "normalized_catalog"]))

# ---------------- Catálogo Mestre FIPE ----------------
from storage.models import VehicleBrand, VehicleModelMaster, VehicleVersion, VehicleCatalogSyncRun
from vehicle_catalog.fipe_full_sync import FipeFullSync
from vehicle_catalog.fipe_incremental_sync import FipeIncrementalSync
from vehicle_catalog.catalog_manifest import CatalogManifestBuilder
from vehicle_catalog.catalog_search_index import CatalogSearchIndexBuilder

@app.get("/catalog/brands")
def catalog_brands(vehicle_type: str | None = None, q: str | None = None, limit: int = Query(100, le=1000)):
    with SessionFactory() as session:
        stmt = select(VehicleBrand)
        if vehicle_type:
            stmt = stmt.where(VehicleBrand.vehicle_type == vehicle_type)
        if q:
            stmt = stmt.where(VehicleBrand.normalized_name.contains(q.lower()))
        return [_serialize(row) for row in session.scalars(stmt.limit(limit)).all()]

@app.get("/catalog/models")
def catalog_models(brand_id: int | None = None, vehicle_type: str | None = None, q: str | None = None, limit: int = Query(100, le=1000)):
    with SessionFactory() as session:
        stmt = select(VehicleModelMaster)
        if brand_id:
            stmt = stmt.where(VehicleModelMaster.brand_id == brand_id)
        if vehicle_type:
            stmt = stmt.where(VehicleModelMaster.vehicle_type == vehicle_type)
        if q:
            stmt = stmt.where(VehicleModelMaster.normalized_name.contains(q.lower()))
        return [_serialize(row) for row in session.scalars(stmt.limit(limit)).all()]

@app.get("/catalog/versions")
def catalog_versions(model_id: int | None = None, vehicle_type: str | None = None, year: int | None = None, fipe_code: str | None = None, limit: int = Query(100, le=1000)):
    with SessionFactory() as session:
        stmt = select(VehicleVersion)
        if model_id:
            stmt = stmt.where(VehicleVersion.model_id == model_id)
        if vehicle_type:
            stmt = stmt.where(VehicleVersion.vehicle_type == vehicle_type)
        if year:
            stmt = stmt.where(VehicleVersion.year == year)
        if fipe_code:
            stmt = stmt.where(VehicleVersion.fipe_code == fipe_code)
        return [_serialize(row) for row in session.scalars(stmt.limit(limit)).all()]

@app.get("/catalog/search")
def catalog_search(q: str, limit: int = Query(20, le=100)):
    return {"query": q, "results": CatalogSearchIndexBuilder().search(q, limit=limit)}

@app.get("/catalog/sync/status")
def catalog_sync_status(limit: int = Query(10, le=100)):
    with SessionFactory() as session:
        rows = session.scalars(select(VehicleCatalogSyncRun).order_by(VehicleCatalogSyncRun.id.desc()).limit(limit)).all()
    manifest_path = Path("exports/catalog_manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else None
    return {"runs": [_serialize(row) for row in rows], "manifest": manifest}

@app.post("/catalog/sync/full")
def catalog_sync_full(vehicle_type: str | None = None, max_brands: int | None = None, max_models: int | None = None, max_versions: int | None = None, confirm_full_sync: bool = False):
    if not confirm_full_sync:
        return {"status": "cancelled", "message": "Full sync cancelada. Envie confirm_full_sync=true para confirmar."}
    types = [vehicle_type] if vehicle_type else None
    result = FipeFullSync().run(vehicle_types=types, max_brands=max_brands, max_models=max_models, max_versions=max_versions)
    CatalogManifestBuilder().export_catalog_tables()
    CatalogSearchIndexBuilder().export()
    return result

@app.post("/catalog/sync/incremental")
def catalog_sync_incremental(vehicle_type: str | None = None, max_brands: int | None = None, max_models: int | None = None, max_versions: int | None = None):
    types = [vehicle_type] if vehicle_type else None
    result = FipeIncrementalSync().run(vehicle_types=types, max_brands=max_brands, max_models=max_models, max_versions=max_versions)
    CatalogManifestBuilder().export_catalog_tables()
    CatalogSearchIndexBuilder().export()
    return result
