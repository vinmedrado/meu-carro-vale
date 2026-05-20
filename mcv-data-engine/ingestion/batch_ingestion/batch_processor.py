from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from ingestion.csv_ingestion.csv_ingestor import CSVIngestor
from ingestion.json_ingestion.json_ingestor import JSONIngestor


@dataclass(slots=True)
class BatchIngestionResult:
    received_files: int
    received_records: int
    records: list[dict]
    errors: list[str]


class BatchIngestionProcessor:
    def __init__(self, chunk_size: int = 2_000):
        self.csv_ingestor = CSVIngestor(chunk_size=chunk_size)
        self.json_ingestor = JSONIngestor()

    def ingest_paths(self, paths: Iterable[str | Path]) -> BatchIngestionResult:
        all_records: list[dict] = []
        errors: list[str] = []
        count = 0
        for raw_path in paths:
            count += 1
            path = Path(raw_path)
            try:
                if path.suffix.lower() == ".csv":
                    all_records.extend(self.csv_ingestor.ingest(path))
                elif path.suffix.lower() == ".json":
                    all_records.extend(self.json_ingestor.ingest(path))
                else:
                    errors.append(f"arquivo_ignorado:{path.name}")
            except Exception as exc:
                errors.append(f"erro:{path.name}:{exc}")
        return BatchIngestionResult(count, len(all_records), all_records, errors)
