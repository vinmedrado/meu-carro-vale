from __future__ import annotations
from pathlib import Path
from collectors.fipe_collector import FipeCollector
from collectors.marketplaces import OlxCollector, WebmotorsCollector, IcarrosCollector, MercadoLivreCollector, KavakCollector
from comparables.comparable_dataset import ComparableDatasetBuilder
from comparables.comparable_intelligence_engine import ComparableIntelligenceEngine
from deduplication.deduplicator import ListingDeduplicator
from ingestion.batch_ingestion.batch_processor import BatchIngestionProcessor
from ingestion.csv_ingestion.csv_ingestor import CSVIngestor
from ingestion.json_ingestion.json_ingestor import JSONIngestor
from ingestion.validators.data_quality_engine import DataQualityEngine
from liquidity.liquidity_calculator import LiquidityCalculator
from market_behavior.market_behavior_engine import MarketBehaviorEngine
from normalizers.vehicle_normalizer import VehicleNormalizer
from snapshots.snapshot_builder import SnapshotBuilder
from storage.exporter import DatasetExporter
from storage.models import init_db, get_session_factory
from storage.quality_repository import MarketQualityAggregator
from storage.repository import Repository


class MCVDataPipeline:
    def __init__(self, export_dir: str | Path = "exports", chunk_size: int = 2_000):
        self.normalizer = VehicleNormalizer()
        self.quality_engine = DataQualityEngine()
        self.deduplicator = ListingDeduplicator()
        self.snapshot_builder = SnapshotBuilder()
        self.liquidity_calculator = LiquidityCalculator()
        self.market_behavior_engine = MarketBehaviorEngine()
        self.comparable_builder = ComparableDatasetBuilder()
        self.comparable_engine = ComparableIntelligenceEngine()
        self.quality_aggregator = MarketQualityAggregator()
        self.exporter = DatasetExporter(export_dir)
        self.csv_ingestor = CSVIngestor(chunk_size=chunk_size)
        self.json_ingestor = JSONIngestor()
        self.batch_processor = BatchIngestionProcessor(chunk_size=chunk_size)

    def run_import(self, path: str | Path, persist: bool = False) -> dict:
        path = Path(path)
        if path.suffix.lower() == ".csv":
            raw_records = self.csv_ingestor.ingest(path)
        elif path.suffix.lower() == ".json":
            raw_records = self.json_ingestor.ingest(path)
        else:
            raise ValueError("Formato suportado: .csv ou .json")
        return self.process_records(raw_records, persist=persist, already_normalized=True)

    def run_batch_import(self, paths: list[str | Path], persist: bool = False) -> dict:
        batch = self.batch_processor.ingest_paths(paths)
        result = self.process_records(batch.records, persist=persist, already_normalized=True)
        result["files_received"] = batch.received_files
        result["batch_errors"] = batch.errors
        return result

    def run_fipe_catalog(self, max_brands: int | None = 2, max_models_per_brand: int | None = 2, persist: bool = False) -> dict:
        result = FipeCollector().collect(max_brands=max_brands, max_models_per_brand=max_models_per_brand)
        normalized = [self.quality_engine.enrich(self.normalizer.normalize(r)) for r in result.records]
        exports = self.exporter.export("vehicle_catalog", normalized)
        if persist:
            engine = init_db()
            session_factory = get_session_factory(engine)
            with session_factory() as session:
                Repository(session).save_vehicle_catalog(normalized)
        return {"records": len(normalized), "errors": result.errors, "exports": exports}

    def run_prepared_collectors(self) -> list[dict]:
        collectors = [OlxCollector(), WebmotorsCollector(), IcarrosCollector(), MercadoLivreCollector(), KavakCollector()]
        return [{"source": c.source, "enabled": c.enabled, "errors": c.collect().errors} for c in collectors]

    def process_records(self, raw_records: list[dict], persist: bool = False, already_normalized: bool = False) -> dict:
        normalized = raw_records if already_normalized else [self.quality_engine.enrich(self.normalizer.normalize(r)) for r in raw_records]
        enriched_for_comparables = self.comparable_builder.enrich_with_group_metrics(normalized)
        deduped = self.deduplicator.deduplicate(enriched_for_comparables)
        snapshots = self.snapshot_builder.build(deduped.clean_records)
        liquidity = self.liquidity_calculator.calculate(snapshots)
        comparables_df = self.comparable_builder.build(deduped.clean_records)
        intelligent_comparables = self.comparable_engine.build_dataset(deduped.clean_records)
        market_quality = self.quality_aggregator.aggregate(normalized)
        market_behavior = self._build_market_behavior_exports(deduped.clean_records, snapshots)
        exports = {
            "market_listings": self.exporter.export("market_listings", deduped.clean_records),
            "market_snapshots": self.exporter.export("market_snapshots", snapshots),
            "snapshots": self.exporter.export("snapshots", snapshots),
            "liquidity": self.exporter.export("liquidity", liquidity),
            "comparables": self.exporter.export("comparables", intelligent_comparables),
            "comparables_base": self.exporter.export("comparables_base", comparables_df),
            "market_quality": self.exporter.export("market_quality", market_quality),
            "market_behavior": self.exporter.export("market_behavior", market_behavior),
            "normalized_catalog": self.exporter.export("normalized_catalog", normalized),
        }
        if persist:
            engine = init_db()
            session_factory = get_session_factory(engine)
            with session_factory() as session:
                repo = Repository(session)
                repo.save_listings(deduped.clean_records)
                repo.save_snapshots(snapshots)
                repo.save_liquidity(liquidity)
                repo.save_market_quality(market_quality)
        return {
            "received": len(raw_records),
            "normalized": len(normalized),
            "clean_records": len(deduped.clean_records),
            "duplicates": len(deduped.duplicates),
            "quality_rows": len(market_quality),
            "avg_quality": self._avg_quality(normalized),
            "snapshots": len(snapshots),
            "liquidity_rows": len(liquidity),
            "comparables_rows": len(intelligent_comparables),
            "market_behavior_rows": len(market_behavior),
            "exports": exports,
        }

    def _avg_quality(self, records: list[dict]) -> float:
        values = [float(r.get("qualidade_dado") or 0) for r in records]
        return round(sum(values) / max(len(values), 1), 3)


    def _build_market_behavior_exports(self, records: list[dict], snapshots: list[dict]) -> list[dict]:
        groups: dict[tuple, dict] = {}
        for snapshot in snapshots:
            key = (snapshot.get("marca"), snapshot.get("modelo"), snapshot.get("versao"), snapshot.get("ano"), snapshot.get("estado") or snapshot.get("regiao"), snapshot.get("cidade"))
            target = {
                "marca": snapshot.get("marca"),
                "modelo": snapshot.get("modelo"),
                "versao": snapshot.get("versao"),
                "ano": snapshot.get("ano"),
                "estado": snapshot.get("estado") or snapshot.get("regiao"),
                "cidade": snapshot.get("cidade"),
                "preco": snapshot.get("preco_mediano"),
            }
            comparables = [
                r for r in records
                if r.get("marca") == target.get("marca")
                and r.get("modelo") == target.get("modelo")
                and (not target.get("ano") or not r.get("ano") or abs(int(r.get("ano")) - int(target.get("ano"))) <= 2)
            ]
            groups[key] = {"target": target, "comparables": comparables, "snapshots": [snapshot]}
        return self.market_behavior_engine.export_rows(list(groups.values()))
