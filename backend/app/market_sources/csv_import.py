from __future__ import annotations

import csv
import io
from app.services.normalization import clean_listing


def parse_market_csv(content: bytes) -> tuple[list, list[str]]:
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    errors: list[str] = []
    for index, row in enumerate(reader, start=2):
        cleaned, error = clean_listing(dict(row))
        if cleaned:
            rows.append(cleaned)
        elif error:
            errors.append(f"Linha {index}: {error}")
    return rows, errors
