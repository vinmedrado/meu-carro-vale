from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from normalizers.vehicle_normalizer import VehicleNormalizer
from ingestion.validators.data_quality_engine import DataQualityEngine


class CSVIngestor:
    def __init__(self, chunk_size: int = 2_000):
        self.chunk_size = chunk_size
        self.normalizer = VehicleNormalizer()
        self.quality = DataQualityEngine()

    def iter_chunks(self, path: str | Path) -> Iterable[list[dict]]:
        path = Path(path)
        for chunk in pd.read_csv(path, chunksize=self.chunk_size):
            records = chunk.where(pd.notna(chunk), None).to_dict(orient="records")
            yield [self.quality.enrich(self.normalizer.normalize(row)) for row in records]

    def ingest(self, path: str | Path) -> list[dict]:
        rows: list[dict] = []
        for chunk in self.iter_chunks(path):
            rows.extend(chunk)
        return rows
