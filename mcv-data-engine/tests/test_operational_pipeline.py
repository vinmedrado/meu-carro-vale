from __future__ import annotations
import json
from pathlib import Path

from pipeline_orchestrator import PipelineOrchestrator
from validation.export_validation_engine import ExportValidationEngine


def test_pipeline_completo_gera_manifest(tmp_path):
    orchestrator = PipelineOrchestrator()
    orchestrator.config.export_dir.mkdir(exist_ok=True)
    result = orchestrator.run(input_path="sample_market_listings.csv")
    assert result["status"] == "completed"
    assert Path("exports/manifest.json").exists()
    manifest = json.loads(Path("exports/manifest.json").read_text(encoding="utf-8"))
    assert manifest["validation_status"] == "aprovado"
    assert any(f["name"] == "comparables" for f in manifest["files"])


def test_execucao_parcial_snapshots_funciona():
    result = PipelineOrchestrator().run(input_path="sample_market_listings.csv", only="snapshots")
    assert result["status"] == "completed"
    step_names = [step["name"] for step in result["steps"]]
    assert "snapshots" in step_names
    assert "final_validation" in step_names


def test_export_validation_engine_valida_schema():
    PipelineOrchestrator().run(input_path="sample_market_listings.csv", only="exports")
    validation = ExportValidationEngine().validate_all(["comparables", "snapshots", "liquidity", "market_behavior", "normalized_catalog"])
    assert validation["validation_status"] == "aprovado"
    assert validation["quality_score"] >= 0.8
