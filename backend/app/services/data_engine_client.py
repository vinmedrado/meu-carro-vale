from __future__ import annotations

import csv
import json
import logging
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class DataEngineStatus:
    available: bool
    mode: str
    source: str
    message: str = ""


class DataEngineContractError(RuntimeError):
    pass


class MCVDataEngineClient:
    """Cliente oficial do mcv-data-engine.

    Suporta dois modos:
    - api: consome a API do data-engine em MCV_DATA_ENGINE_API_URL;
    - files: lê exports parquet/csv em MCV_DATA_ENGINE_EXPORTS_PATH.

    O cliente nunca inventa dado real. Quando não encontra fonte válida, retorna vazio
    com motivo explícito para que o valuation use fallback seguro e sinalize baixa amostra.
    """

    def __init__(self, mode: str | None = None, api_url: str | None = None, exports_path: str | None = None, timeout: float = 3.5):
        self.mode = (mode or settings.data_engine_mode or "files").strip().lower()
        self.api_url = (api_url or settings.data_engine_api_url or "http://127.0.0.1:8020").rstrip("/")
        self.exports_path = Path(exports_path or settings.data_engine_exports_path)
        self.timeout = timeout

    def status(self) -> DataEngineStatus:
        if self.mode == "api":
            try:
                payload = self._get_json("/health", {})
                if payload.get("status") == "ok":
                    return DataEngineStatus(True, "api", self.api_url, "Motor de dados disponível por API.")
            except Exception as exc:  # noqa: BLE001
                return DataEngineStatus(False, "api", self.api_url, f"Motor de dados indisponível: {exc}")
        manifest = self.load_manifest()
        if manifest:
            return DataEngineStatus(True, "files", str(self.exports_path), "Exports locais disponíveis.")
        return DataEngineStatus(False, self.mode, str(self.exports_path), "Nenhum manifest/export válido encontrado.")

    def load_manifest(self) -> dict[str, Any]:
        if self.mode == "api":
            try:
                return self._get_json("/ops/exports/manifest", {})
            except Exception:
                return {}
        for name in ("manifest.json", "catalog_manifest.json"):
            path = self.exports_path / name
            if path.exists():
                try:
                    return json.loads(path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    logger.warning("Manifest inválido em %s", path)
        return {}

    def search_catalog(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        query = (query or "").strip()
        if len(query) < 2:
            return []
        if self.mode == "api":
            try:
                payload = self._get_json("/catalog/search", {"q": query, "limit": limit})
                results = payload.get("results", payload if isinstance(payload, list) else [])
                return [self._normalize_search_result(item) for item in results][:limit]
            except Exception as exc:  # noqa: BLE001
                logger.warning("Falha na busca via API do data-engine: %s. Tentando exports locais.", exc)
                return MCVDataEngineClient(mode="files", exports_path=str(self.exports_path))._search_catalog_files(query, limit=limit)
        return self._search_catalog_files(query, limit=limit)

    def get_comparables(self, vehicle: dict[str, Any], limit: int = 20) -> dict[str, Any]:
        params = self._vehicle_params(vehicle) | {"limit": limit}
        if self.mode == "api":
            try:
                payload = self._get_json("/market/comparables", params)
                self._validate_mapping(payload, ["comparables"])
                return payload
            except Exception as exc:  # noqa: BLE001
                logger.warning("Falha ao obter comparáveis via API: %s", exc)
                return self._empty_payload("comparables", str(exc))
        return self._comparables_from_files(vehicle, limit)

    def get_liquidity(self, vehicle: dict[str, Any]) -> dict[str, Any]:
        if self.mode == "api":
            try:
                return self._get_json("/market/liquidity", self._vehicle_params(vehicle))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Falha ao obter liquidez via API: %s", exc)
                return self._empty_payload("liquidity", str(exc))
        rows = self._read_export("liquidity")
        return {"liquidity": self._best_rows(rows, vehicle, limit=10), "source": "exports"}

    def get_behavior(self, vehicle: dict[str, Any]) -> dict[str, Any]:
        if self.mode == "api":
            try:
                return self._get_json("/market/behavior", self._vehicle_params(vehicle))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Falha ao obter comportamento via API: %s", exc)
                return self._empty_payload("behavior", str(exc))
        rows = self._read_export("market_behavior")
        return {"behavior": self._best_rows(rows, vehicle, limit=5), "source": "exports"}

    def get_snapshots(self, vehicle: dict[str, Any]) -> dict[str, Any]:
        if self.mode == "api":
            try:
                return self._get_json("/market/snapshots", self._vehicle_params(vehicle))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Falha ao obter snapshots via API: %s", exc)
                return self._empty_payload("snapshots", str(exc))
        rows = self._read_export("snapshots") or self._read_export("market_snapshots")
        return {"snapshots": self._best_rows(rows, vehicle, limit=20), "source": "exports"}

    def resolve_vehicle(self, query: str) -> dict[str, Any] | None:
        results = self.search_catalog(query, limit=1)
        return results[0] if results else None

    def _get_json(self, path: str, params: dict[str, Any]) -> dict[str, Any] | list[Any]:
        url = f"{self.api_url}{path}"
        clean = {k: v for k, v in params.items() if v not in (None, "")}
        if clean:
            url = f"{url}?{urllib.parse.urlencode(clean)}"
        request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "MeuCarroVale/1.0"})
        with urllib.request.urlopen(request, timeout=self.timeout) as response:  # noqa: S310 - URL configurável pelo operador local
            return json.loads(response.read().decode("utf-8"))

    def _search_catalog_files(self, query: str, limit: int) -> list[dict[str, Any]]:
        rows = self._read_export("vehicle_search_index") or self._build_search_rows_from_catalog_files()
        q = self._norm(query)
        scored: list[tuple[int, dict[str, Any]]] = []
        for row in rows:
            text = self._norm(" ".join(str(row.get(k, "")) for k in ("display_name", "marca", "brand", "modelo", "model", "versao", "version", "ano", "year", "alias")))
            if not text:
                continue
            tokens = [t for t in q.split() if len(t) > 1]
            hits = sum(1 for t in tokens if t in text)
            if q in text:
                hits += 4
            if hits:
                scored.append((min(99, 55 + hits * 8), row))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [self._normalize_search_result(row, confidence=score) for score, row in scored[:limit]]

    def _build_search_rows_from_catalog_files(self) -> list[dict[str, Any]]:
        versions = self._read_export("vehicle_versions") or self._read_export("vehicle_catalog_full") or self._read_export("normalized_catalog")
        return versions

    def _comparables_from_files(self, vehicle: dict[str, Any], limit: int) -> dict[str, Any]:
        rows = self._read_export("comparables") or self._read_export("comparables_base") or self._read_export("market_listings")
        selected = self._best_rows(rows, vehicle, limit=limit)
        prices = [float(r.get("preco_comparavel") or r.get("preco") or r.get("price") or 0) for r in selected if r.get("preco_comparavel") or r.get("preco") or r.get("price")]
        stats = {}
        if prices:
            prices_sorted = sorted(prices)
            mid = len(prices_sorted) // 2
            stats = {
                "quantidade_comparaveis": len(prices),
                "preco_minimo": min(prices),
                "preco_mediano": prices_sorted[mid],
                "preco_maximo": max(prices),
                "confianca_amostra": "Alta" if len(prices) >= 8 else "Média" if len(prices) >= 4 else "Baixa",
            }
        return {"comparables": selected, "sample_statistics": stats, "source": "exports"}

    def _read_export(self, stem: str) -> list[dict[str, Any]]:
        parquet = self.exports_path / f"{stem}.parquet"
        csv_path = self.exports_path / f"{stem}.csv"
        try:
            if parquet.exists():
                return pd.read_parquet(parquet).fillna("").to_dict(orient="records")
            if csv_path.exists():
                with csv_path.open("r", encoding="utf-8") as fh:
                    return list(csv.DictReader(fh))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Falha ao ler export %s: %s", stem, exc)
        return []

    def _best_rows(self, rows: list[dict[str, Any]], vehicle: dict[str, Any], limit: int = 10) -> list[dict[str, Any]]:
        if not rows:
            return []
        target_brand = self._norm(vehicle.get("brand") or vehicle.get("marca"))
        target_model = self._norm(vehicle.get("model") or vehicle.get("modelo"))
        target_state = self._norm(vehicle.get("state") or vehicle.get("estado"))
        scored = []
        for row in rows:
            score = 0
            if target_brand and target_brand in self._norm(row.get("brand") or row.get("marca")):
                score += 4
            if target_model and target_model in self._norm(row.get("model") or row.get("modelo")):
                score += 6
            if target_state and target_state == self._norm(row.get("state") or row.get("estado")):
                score += 2
            scored.append((score, row))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [row for score, row in scored[:limit] if score > 0] or [row for _, row in scored[:limit]]

    def _vehicle_params(self, vehicle: dict[str, Any]) -> dict[str, Any]:
        return {
            "brand": vehicle.get("brand") or vehicle.get("marca"),
            "model": vehicle.get("model") or vehicle.get("modelo"),
            "version": vehicle.get("version") or vehicle.get("versao"),
            "year": vehicle.get("year") or vehicle.get("ano"),
            "mileage": vehicle.get("km") or vehicle.get("mileage"),
            "state": vehicle.get("state") or vehicle.get("estado"),
            "city": vehicle.get("city") or vehicle.get("cidade"),
        }

    def _normalize_search_result(self, item: dict[str, Any], confidence: int | None = None) -> dict[str, Any]:
        brand = item.get("brand") or item.get("marca") or item.get("canonical_brand") or item.get("brand_name") or item.get("marca_nome") or ""
        model = item.get("model") or item.get("modelo") or item.get("canonical_model") or item.get("model_name") or item.get("modelo_nome") or ""
        version = item.get("version") or item.get("versao") or item.get("version_name") or item.get("normalized_version_name") or ""
        year = item.get("year") or item.get("ano") or ""
        fuel = item.get("fuel") or item.get("combustivel") or ""
        fipe_code = item.get("fipe_code") or item.get("codigo_fipe") or ""
        display = item.get("display_name") or " ".join(str(x) for x in [brand, model, version, year] if x).strip()
        return {
            "brand": brand,
            "model": model,
            "version": version,
            "year": int(year) if str(year).isdigit() else year,
            "fuel": fuel,
            "fipe_code": fipe_code,
            "confidence": int(confidence or item.get("confidence") or item.get("score") or item.get("similarity") or 80),
            "display_name": display,
            "source": item.get("source") or item.get("fonte") or "mcv-data-engine",
            "raw": item,
        }

    def _validate_mapping(self, payload: Any, required: list[str]) -> None:
        if not isinstance(payload, dict):
            raise DataEngineContractError("Resposta do motor de dados não é um objeto JSON.")
        missing = [field for field in required if field not in payload]
        if missing:
            raise DataEngineContractError(f"Resposta do motor de dados sem campos obrigatórios: {', '.join(missing)}")

    def _empty_payload(self, key: str, reason: str) -> dict[str, Any]:
        return {key: [] if key.endswith("s") or key in {"comparables", "snapshots"} else {}, "source": "fallback", "warning": reason}

    def _norm(self, value: Any) -> str:
        import re
        import unicodedata
        text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii").lower()
        return re.sub(r"[^a-z0-9]+", " ", text).strip()
