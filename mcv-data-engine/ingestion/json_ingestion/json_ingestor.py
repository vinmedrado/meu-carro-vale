from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from normalizers.vehicle_normalizer import VehicleNormalizer
from ingestion.validators.data_quality_engine import DataQualityEngine


class JSONIngestor:
    def __init__(self):
        self.normalizer = VehicleNormalizer()
        self.quality = DataQualityEngine()

    def ingest(self, path: str | Path) -> list[dict[str, Any]]:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            records = payload.get("records") or payload.get("data") or payload.get("listings") or []
        else:
            records = payload
        if not isinstance(records, list):
            raise ValueError("JSON precisa conter uma lista ou uma chave records/data/listings.")
        return [self.quality.enrich(self.normalizer.normalize(row)) for row in records]
