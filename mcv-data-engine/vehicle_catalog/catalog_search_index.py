from __future__ import annotations
from pathlib import Path
import pandas as pd
from sqlalchemy import select
from storage.models import VehicleBrand, VehicleModelMaster, VehicleVersion, init_db, get_session_factory
from .catalog_normalizer import normalize_text, BRAND_ALIASES, MODEL_ALIASES

class CatalogSearchIndexBuilder:
    def __init__(self, export_dir: str | Path = "exports"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def build_rows(self) -> list[dict]:
        engine = init_db()
        Session = get_session_factory(engine)
        rows: list[dict] = []
        with Session() as session:
            versions = session.scalars(select(VehicleVersion).limit(1_000_000)).all()
            for version in versions:
                brand = session.get(VehicleBrand, version.brand_id)
                model = session.get(VehicleModelMaster, version.model_id)
                if not brand or not model:
                    continue
                aliases = self._aliases_for(brand.canonical_name, model.canonical_name, version.version_name)
                search_text = " ".join([brand.canonical_name, model.canonical_name, version.version_name or "", str(version.year or ""), version.fuel or "", version.fipe_code or "", *aliases])
                rows.append({
                    "vehicle_type": version.vehicle_type,
                    "marca": brand.canonical_name,
                    "modelo": model.canonical_name,
                    "versao": version.version_name,
                    "ano": version.year,
                    "combustivel": version.fuel,
                    "codigo_fipe": version.fipe_code,
                    "alias": ", ".join(aliases),
                    "search_text": normalize_text(search_text),
                })
        return rows

    def search(self, query: str, limit: int = 20) -> list[dict]:
        tokens = normalize_text(query).split()
        rows = self.build_rows()
        scored: list[tuple[int, dict]] = []
        for row in rows:
            text = row.get("search_text", "")
            score = sum(1 for token in tokens if token in text)
            if score:
                scored.append((score, row))
        return [r for _, r in sorted(scored, key=lambda x: x[0], reverse=True)[:limit]]

    def export(self) -> dict[str, str]:
        df = pd.DataFrame(self.build_rows())
        csv_path = self.export_dir / "vehicle_search_index.csv"
        df.to_csv(csv_path, index=False)
        paths = {"csv": str(csv_path)}
        try:
            parquet_path = self.export_dir / "vehicle_search_index.parquet"
            df.to_parquet(parquet_path, index=False)
            paths["parquet"] = str(parquet_path)
        except Exception:
            paths["parquet"] = "parquet indisponível: instale pyarrow"
        return paths

    def _aliases_for(self, brand: str, model: str, version: str | None) -> list[str]:
        normalized_brand = normalize_text(brand)
        normalized_model = normalize_text(model)
        aliases = [alias for alias, canonical in BRAND_ALIASES.items() if canonical == normalized_brand]
        aliases += [alias for alias, canonical in MODEL_ALIASES.items() if canonical == normalized_model]
        version_text = normalize_text(version)
        if "agile" in f"{normalized_model} {version_text}":
            aliases += ["agile ltz", "agile lt", "agile effect"]
        if normalized_model == "classic":
            aliases += ["corsa classic"]
        return sorted(set(aliases))
