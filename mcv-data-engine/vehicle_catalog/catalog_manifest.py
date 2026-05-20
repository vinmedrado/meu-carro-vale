from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
from sqlalchemy import func, select
from storage.models import VehicleBrand, VehicleModelMaster, VehicleVersion, VehicleCatalogSyncRun, init_db, get_session_factory

class CatalogManifestBuilder:
    def __init__(self, export_dir: str | Path = "exports"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def build(self, mode: str | None = None, stats: dict | None = None, totals: dict | None = None, exports: dict | None = None) -> dict:
        engine = init_db()
        Session = get_session_factory(engine)
        with Session() as session:
            total_brands = session.scalar(select(func.count()).select_from(VehicleBrand)) or 0
            total_models = session.scalar(select(func.count()).select_from(VehicleModelMaster)) or 0
            total_versions = session.scalar(select(func.count()).select_from(VehicleVersion)) or 0
            latest_run = session.scalar(select(VehicleCatalogSyncRun).order_by(VehicleCatalogSyncRun.id.desc()).limit(1))
            reference_month = session.scalar(select(VehicleVersion.reference_month).where(VehicleVersion.reference_month.isnot(None)).order_by(VehicleVersion.updated_at.desc()).limit(1))
            latest_stats = stats or {}
            latest_totals = totals or {}
            payload = {
                "status": latest_run.status if latest_run else "sem_sincronizacao",
                "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                "schema_version": "catalog.v2",
                "modo_execucao": mode or (latest_run.run_type if latest_run else None),
                "total_marcas": int(total_brands),
                "total_modelos": int(total_models),
                "total_versoes": int(total_versions),
                "total_marcas_encontradas": int(latest_totals.get("brands", latest_run.total_brands_found if latest_run else 0) or 0),
                "total_modelos_encontrados": int(latest_totals.get("models", latest_run.total_models_found if latest_run else 0) or 0),
                "total_versoes_encontradas": int(latest_totals.get("versions", latest_run.total_versions_found if latest_run else 0) or 0),
                "ultima_sincronizacao": latest_run.finished_at.isoformat() if latest_run and latest_run.finished_at else None,
                "novos_registros": int(sum(int(latest_stats.get(k, 0) or 0) for k in ["new_brands", "new_models", "new_versions"]) if latest_stats else ((latest_run.new_brands + latest_run.new_models + latest_run.new_versions) if latest_run else 0)),
                "atualizados": int(sum(int(latest_stats.get(k, 0) or 0) for k in ["updated_brands", "updated_models", "updated_versions"]) if latest_stats else ((latest_run.updated_brands + latest_run.updated_models + latest_run.updated_versions) if latest_run else 0)),
                "skipped": int(latest_stats.get("skipped_existing", latest_run.skipped_existing if latest_run else 0) if latest_stats or latest_run else 0),
                "erros": int(latest_stats.get("failed_items", latest_run.failed_items if latest_run else 0) if latest_stats or latest_run else 0),
                "duracao": self._duration(latest_run),
                "mes_referencia": reference_month,
                "status_final": latest_run.status if latest_run else "sem_sincronizacao",
                "exports": exports or {},
            }
        path = self.export_dir / "catalog_manifest.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload

    def export_catalog_tables(self) -> dict[str, dict[str, str]]:
        engine = init_db()
        outputs: dict[str, dict[str, str]] = {}
        queries = {
            "vehicle_brands": "select * from vehicle_brands",
            "vehicle_models": "select * from vehicle_models",
            "vehicle_versions": "select * from vehicle_versions",
        }
        for name, sql in queries.items():
            df = pd.read_sql(sql, engine)
            outputs[name] = self._write_df(name, df)
        full_sql = """
            select b.vehicle_type, b.canonical_name as marca, m.canonical_name as modelo,
                   v.version_name as versao, v.year as ano, v.fuel as combustivel,
                   v.fipe_code as codigo_fipe, v.reference_month as mes_referencia, v.fipe_price as valor_fipe,
                   b.normalized_name as marca_normalizada, m.normalized_name as modelo_normalizado, v.normalized_version_name as versao_normalizada
            from vehicle_versions v
            join vehicle_brands b on b.id = v.brand_id
            join vehicle_models m on m.id = v.model_id
        """
        outputs["vehicle_catalog_full"] = self._write_df("vehicle_catalog_full", pd.read_sql(full_sql, engine))
        return outputs

    def _write_df(self, name: str, df: pd.DataFrame) -> dict[str, str]:
        self.export_dir.mkdir(parents=True, exist_ok=True)
        paths: dict[str, str] = {}
        csv_path = self.export_dir / f"{name}.csv"
        df.to_csv(csv_path, index=False)
        paths["csv"] = str(csv_path)
        try:
            parquet_path = self.export_dir / f"{name}.parquet"
            df.to_parquet(parquet_path, index=False)
            paths["parquet"] = str(parquet_path)
        except Exception:
            paths["parquet"] = "parquet indisponível: instale pyarrow"
        return paths

    def _duration(self, run) -> float | None:
        if not run or not run.finished_at or not run.started_at:
            return None
        return round((run.finished_at - run.started_at).total_seconds(), 3)
