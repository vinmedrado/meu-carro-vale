from __future__ import annotations

from typing import Any

import httpx

from collectors.base import ResponsibleHttpClient
from ingestion.validators.data_quality_engine import DataQualityEngine
from normalizers.vehicle_normalizer import VehicleNormalizer


class APIIngestor:
    """Cliente genérico para APIs autorizadas/futuras.

    Não faz scraping: consome endpoints estruturados quando houver permissão ou contrato.
    """

    def __init__(self, base_url: str, timeout: float = 20.0):
        self.base_url = base_url.rstrip("/")
        self.client = ResponsibleHttpClient(timeout=timeout)
        self.normalizer = VehicleNormalizer()
        self.quality = DataQualityEngine()

    def fetch_records(self, path: str, params: dict[str, Any] | None = None, records_key: str | None = None) -> list[dict]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = httpx.get(url, params=params, timeout=20.0)
        response.raise_for_status()
        payload = response.json()
        records = payload.get(records_key) if records_key and isinstance(payload, dict) else payload
        if isinstance(records, dict):
            records = records.get("records") or records.get("data") or []
        if not isinstance(records, list):
            raise ValueError("API não retornou uma lista de registros.")
        return [self.quality.enrich(self.normalizer.normalize(row)) for row in records]
