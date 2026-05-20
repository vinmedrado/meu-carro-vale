from __future__ import annotations
from dataclasses import asdict
from datetime import datetime, date, timezone
from pathlib import Path
from typing import Any
import json
import pandas as pd

from contracts.export_contracts import EXPORT_CONTRACTS, ExportContract, ColumnContract, get_contract


class ExportValidationEngine:
    def __init__(self, export_dir: str | Path = "exports"):
        self.export_dir = Path(export_dir)

    def validate_all(self, names: list[str] | None = None) -> dict[str, Any]:
        selected = names or list(EXPORT_CONTRACTS.keys())
        validations = {name: self.validate_export(name) for name in selected}
        avg_quality = round(sum(v["quality_score"] for v in validations.values()) / max(len(validations), 1), 3)
        status = "aprovado" if all(v["validation_status"] == "aprovado" for v in validations.values()) else "atenção"
        return {"validation_status": status, "quality_score": avg_quality, "exports": validations}

    def validate_export(self, name: str) -> dict[str, Any]:
        contract = get_contract(name)
        if not contract:
            return self._result(name, "ignorado", [f"Contrato inexistente para {name}"], 0.0, 0)
        path = self._resolve_file(name)
        if not path:
            return self._result(name, "erro", [f"Arquivo {name}.parquet ou {name}.csv não encontrado"], 0.0, 0, contract)
        try:
            df = self._read(path)
        except Exception as exc:
            return self._result(name, "erro", [f"Falha ao ler export: {exc}"], 0.0, 0, contract, str(path))
        errors: list[str] = []
        warnings: list[str] = []
        if df.empty:
            errors.append("Arquivo está vazio")
        self._validate_schema(df, contract, errors, warnings)
        self._validate_ranges(df, contract, errors, warnings)
        self._validate_duplicates(df, contract, warnings)
        penalty = len(errors) * 0.22 + len(warnings) * 0.05
        quality = round(max(0.0, min(1.0, 1.0 - penalty)), 3)
        status = "aprovado" if not errors else "erro"
        return self._result(name, status, errors, quality, int(len(df)), contract, str(path), warnings)

    def write_manifest(self, validation: dict[str, Any] | None = None) -> dict[str, Any]:
        validation = validation or self.validate_all()
        files = []
        for name, result in validation.get("exports", {}).items():
            path = result.get("path")
            files.append({
                "name": name,
                "path": path,
                "records": result.get("records", 0),
                "schema_version": result.get("schema_version"),
                "quality_score": result.get("quality_score"),
                "validation_status": result.get("validation_status"),
            })
        manifest = {
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "schema_registry_version": "1.0.0",
            "validation_status": validation.get("validation_status"),
            "quality_score": validation.get("quality_score"),
            "files": files,
            "snapshots_available": self._snapshots_available(),
        }
        self.export_dir.mkdir(parents=True, exist_ok=True)
        path = self.export_dir / "manifest.json"
        path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        return manifest

    def _resolve_file(self, name: str) -> Path | None:
        candidates = [self.export_dir / f"{name}.parquet", self.export_dir / f"{name}.csv"]
        if name == "catalog":
            candidates += [self.export_dir / "vehicle_catalog.parquet", self.export_dir / "vehicle_catalog.csv", self.export_dir / "normalized_catalog.parquet", self.export_dir / "normalized_catalog.csv"]
        return next((p for p in candidates if p.exists()), None)

    def _read(self, path: Path) -> pd.DataFrame:
        if path.suffix == ".parquet":
            return pd.read_parquet(path)
        return pd.read_csv(path)

    def _validate_schema(self, df: pd.DataFrame, contract: ExportContract, errors: list[str], warnings: list[str]) -> None:
        for column in contract.columns:
            if column.name not in df.columns:
                (errors if column.required else warnings).append(f"Coluna ausente: {column.name}")

    def _validate_ranges(self, df: pd.DataFrame, contract: ExportContract, errors: list[str], warnings: list[str]) -> None:
        for column in contract.columns:
            if column.name not in df.columns or df.empty:
                continue
            series = df[column.name]
            if column.required and series.isna().any():
                errors.append(f"Coluna obrigatória com nulos: {column.name}")
            if column.dtype in {"integer", "float"}:
                numeric = pd.to_numeric(series, errors="coerce")
                if column.required and numeric.isna().any():
                    errors.append(f"Coluna numérica inválida: {column.name}")
                valid = numeric.dropna()
                if column.min_value is not None and (valid < column.min_value).any():
                    errors.append(f"Valores abaixo do mínimo em {column.name}")
                if column.max_value is not None and (valid > column.max_value).any():
                    errors.append(f"Valores acima do máximo em {column.name}")

    def _validate_duplicates(self, df: pd.DataFrame, contract: ExportContract, warnings: list[str]) -> None:
        cols = [c for c in contract.primary_columns if c in df.columns]
        if cols and df.duplicated(subset=cols).any():
            warnings.append(f"Duplicidades detectadas na chave: {', '.join(cols)}")

    def _snapshots_available(self) -> list[str]:
        path = self._resolve_file("snapshots")
        if not path:
            return []
        try:
            df = self._read(path)
            if "mes" in df.columns:
                return sorted([str(v) for v in df["mes"].dropna().unique().tolist()])
        except Exception:
            return []
        return []

    def _result(self, name: str, status: str, errors: list[str], quality: float, records: int, contract: ExportContract | None = None, path: str | None = None, warnings: list[str] | None = None) -> dict[str, Any]:
        return {
            "name": name,
            "path": path,
            "validation_status": status,
            "validation_errors": errors,
            "validation_warnings": warnings or [],
            "quality_score": quality,
            "records": records,
            "schema_version": contract.schema_version if contract else None,
        }
