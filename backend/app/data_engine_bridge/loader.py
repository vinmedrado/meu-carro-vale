from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.data_engine_bridge.contracts import EXPORT_CONTRACTS, missing_columns

try:  # pandas/pyarrow are optional at import time, mandatory only when parquet/csv is read.
    import pandas as pd
except Exception:  # pragma: no cover
    pd = None  # type: ignore


@dataclass
class ExportValidationResult:
    available: bool
    status: str
    errors: list[str]
    manifest: dict[str, Any]
    files: dict[str, dict[str, Any]]


class DataEngineExportLoader:
    """Leitor oficial dos exports/contratos gerados pelo mcv-data-engine.

    A aplicação principal não coleta dados. Ela apenas consome os arquivos prontos
    do data engine, valida schema mínimo e devolve fallback seguro quando os dados
    não existem ou não são compatíveis.
    """

    def __init__(self, exports_path: str | os.PathLike[str] | None = None):
        raw_path = exports_path or os.getenv("MCV_DATA_ENGINE_EXPORTS_PATH") or "../mcv-data-engine/exports"
        self.exports_path = self._resolve_exports_path(raw_path)

    def _resolve_exports_path(self, raw_path: str | os.PathLike[str]) -> Path:
        path = Path(raw_path).expanduser()
        if path.is_absolute():
            return path.resolve()
        cwd_candidate = path.resolve()
        if cwd_candidate.exists():
            return cwd_candidate
        # backend/app/data_engine_bridge/loader.py -> projeto Meu Carro Vale
        app_root = Path(__file__).resolve().parents[3]
        project_root = Path(__file__).resolve().parents[4]
        candidates = [
            (project_root / path).resolve(),
            (project_root.parent / path).resolve(),
            (project_root / "mcv-data-engine" / "exports").resolve(),
            (project_root.parent / "mcv-data-engine" / "exports").resolve(),
            (app_root / path).resolve(),
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return cwd_candidate

    def manifest_path(self) -> Path:
        return self.exports_path / "manifest.json"

    def load_manifest(self) -> dict[str, Any]:
        path = self.manifest_path()
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"validation_status": "erro", "errors": ["manifest.json inválido"]}

    def validate_exports(self) -> ExportValidationResult:
        errors: list[str] = []
        manifest = self.load_manifest()
        if not self.exports_path.exists():
            errors.append(f"Diretório de exports não encontrado: {self.exports_path}")
        if not manifest:
            errors.append("manifest.json ausente ou vazio")
        files: dict[str, dict[str, Any]] = {}
        for name, contract in EXPORT_CONTRACTS.items():
            try:
                df = self.read_export(name)
            except Exception as exc:
                errors.append(f"{name}: falha ao ler export ({exc})")
                continue
            if df.empty:
                errors.append(f"{name}: arquivo vazio")
            miss = missing_columns(df.columns, contract)
            if miss:
                errors.append(f"{name}: colunas obrigatórias ausentes: {', '.join(miss)}")
            for col in contract.numeric_columns:
                if col in df.columns:
                    converted = pd.to_numeric(df[col], errors="coerce") if pd is not None else []
                    if hasattr(converted, "isna") and converted.isna().all():
                        errors.append(f"{name}: coluna numérica inválida: {col}")
            files[name] = {"records": int(len(df)), "columns": list(map(str, df.columns))}
        status = "aprovado" if not errors else "reprovado"
        return ExportValidationResult(available=not errors, status=status, errors=errors, manifest=manifest, files=files)

    @lru_cache(maxsize=12)
    def read_export(self, name: str):
        if pd is None:
            raise RuntimeError("pandas não está instalado; instale pandas e pyarrow para ler exports do mcv-data-engine")
        parquet_path = self.exports_path / f"{name}.parquet"
        csv_path = self.exports_path / f"{name}.csv"
        if parquet_path.exists():
            try:
                return pd.read_parquet(parquet_path)
            except Exception:
                if not csv_path.exists():
                    raise
        if csv_path.exists():
            return pd.read_csv(csv_path)
        raise FileNotFoundError(f"Export não encontrado: {name}.parquet/.csv")

    def safe_read_export(self, name: str):
        try:
            return self.read_export(name)
        except Exception:
            if pd is None:
                return []
            return pd.DataFrame()
