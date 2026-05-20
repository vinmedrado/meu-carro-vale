from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Any
import json
import traceback

from config.pipeline_config import PipelineConfig, get_pipeline_config
from jobs.pipeline import MCVDataPipeline
from validation.export_validation_engine import ExportValidationEngine
from vehicle_catalog.fipe_incremental_sync import FipeIncrementalSync
from vehicle_catalog.catalog_manifest import CatalogManifestBuilder
from vehicle_catalog.catalog_search_index import CatalogSearchIndexBuilder


@dataclass
class PipelineStepResult:
    name: str
    status: str
    started_at: str
    finished_at: str
    duration_seconds: float
    metrics: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


class PipelineOrchestrator:
    STEPS = [
        "catalog_sync",
        "ingestion",
        "validation",
        "normalization",
        "deduplication",
        "snapshots",
        "comparables",
        "liquidity",
        "behavior",
        "exports",
        "final_validation",
    ]
    ALIASES = {"market_behavior": "behavior", "validate": "final_validation", "all": "all", "catalog": "catalog_sync"}

    def __init__(self, config: PipelineConfig | None = None):
        self.config = config or get_pipeline_config()
        self.pipeline = MCVDataPipeline(export_dir=self.config.export_dir, chunk_size=self.config.batch_size)
        self.validator = ExportValidationEngine(self.config.export_dir)
        self.config.log_dir.mkdir(parents=True, exist_ok=True)
        self._last_processing: dict[str, Any] | None = None

    def run(self, input_path: str | Path | None = None, only: str | None = None, persist: bool = False) -> dict[str, Any]:
        requested = self._selected_steps(only)
        run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        results: list[PipelineStepResult] = []
        context: dict[str, Any] = {"input_path": str(input_path or self.config.default_input), "persist": persist}
        for step in requested:
            results.append(self._run_step(step, lambda s=step: self._execute_step(s, context)))
        summary = {
            "run_id": run_id,
            "status": "completed" if all(r.status == "success" for r in results) else "partial_success",
            "started_at": results[0].started_at if results else datetime.now(timezone.utc).isoformat(),
            "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "steps": [r.__dict__ for r in results],
            "manifest_path": str(self.config.export_dir / "manifest.json"),
        }
        self._write_log(run_id, summary)
        return summary

    def _selected_steps(self, only: str | None) -> list[str]:
        if not only:
            return self.STEPS
        only = self.ALIASES.get(only, only)
        if only == "all":
            return self.STEPS
        if only not in self.STEPS:
            raise ValueError(f"Etapa inválida: {only}. Use uma destas: {', '.join(self.STEPS)}")
        if only in {"snapshots", "comparables", "liquidity", "behavior", "exports"}:
            return ["ingestion", only, "exports", "final_validation"] if only != "exports" else ["ingestion", "exports", "final_validation"]
        if only == "final_validation":
            return ["final_validation"]
        return [only]

    def _run_step(self, name: str, fn: Callable[[], dict[str, Any]]) -> PipelineStepResult:
        started = datetime.now(timezone.utc)
        last_error: Exception | None = None
        for attempt in range(self.config.retries + 1):
            try:
                metrics = fn()
                finished = datetime.now(timezone.utc)
                return PipelineStepResult(
                    name=name,
                    status="success",
                    started_at=started.isoformat(timespec="seconds").replace("+00:00", "Z"),
                    finished_at=finished.isoformat(timespec="seconds").replace("+00:00", "Z"),
                    duration_seconds=round((finished - started).total_seconds(), 3),
                    metrics=metrics,
                )
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt >= self.config.retries:
                    break
        finished = datetime.now(timezone.utc)
        return PipelineStepResult(
            name=name,
            status="error",
            started_at=started.isoformat(timespec="seconds").replace("+00:00", "Z"),
            finished_at=finished.isoformat(timespec="seconds").replace("+00:00", "Z"),
            duration_seconds=round((finished - started).total_seconds(), 3),
            error=f"{last_error}\n{traceback.format_exc(limit=4)}",
        )

    def _execute_step(self, step: str, context: dict[str, Any]) -> dict[str, Any]:
        input_path = Path(context["input_path"])
        if step == "catalog_sync":
            # Incremental seguro por padrão. Em ambiente offline, mantém o pipeline íntegro
            # e registra aviso em vez de quebrar exports existentes.
            try:
                result = FipeIncrementalSync().run(vehicle_types=["carros"], max_brands=1, max_models=1, max_versions=1)
                CatalogManifestBuilder().export_catalog_tables()
                CatalogSearchIndexBuilder().export()
                return {"status": result.get("status"), "novos": result.get("stats", {}).get("new_versions", 0), "atualizados": result.get("stats", {}).get("updated_versions", 0)}
            except Exception as exc:  # noqa: BLE001
                return {"status": "skipped_offline_or_unavailable", "warning": str(exc), "novos": 0, "atualizados": 0}
        if step == "ingestion":
            self._last_processing = self.pipeline.run_import(input_path, persist=bool(context.get("persist")))
            return self._summarize_processing(self._last_processing)
        if step in {"validation", "normalization", "deduplication", "snapshots", "comparables", "liquidity", "behavior", "exports"}:
            if self._last_processing is None:
                self._last_processing = self.pipeline.run_import(input_path, persist=bool(context.get("persist")))
            metric_map = {
                "validation": ["received", "normalized", "avg_quality", "quality_rows"],
                "normalization": ["normalized", "avg_quality"],
                "deduplication": ["clean_records", "duplicates"],
                "snapshots": ["snapshots"],
                "comparables": ["comparables_rows"],
                "liquidity": ["liquidity_rows"],
                "behavior": ["market_behavior_rows"],
                "exports": ["exports"],
            }
            return {k: self._last_processing.get(k) for k in metric_map[step]}
        if step == "final_validation":
            validation = self.validator.validate_all(["comparables", "liquidity", "market_behavior", "snapshots", "normalized_catalog"])
            manifest = self.validator.write_manifest(validation)
            if self.config.fail_on_validation_error and validation.get("validation_status") != "aprovado":
                raise RuntimeError(f"Validação final reprovada: {validation}")
            return {"validation_status": validation.get("validation_status"), "quality_score": validation.get("quality_score"), "manifest_files": len(manifest.get("files", []))}
        raise ValueError(f"Etapa não implementada: {step}")

    def _summarize_processing(self, result: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in result.items() if k != "exports"}

    def _write_log(self, run_id: str, summary: dict[str, Any]) -> None:
        path = self.config.log_dir / f"pipeline_{run_id}.json"
        path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
