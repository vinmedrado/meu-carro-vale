from __future__ import annotations
import json
from pathlib import Path
import pandas as pd


def import_csv(path: str | Path) -> list[dict]:
    df = pd.read_csv(path)
    return df.to_dict(orient="records")


def import_json(path: str | Path) -> list[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = data.get("items") or data.get("records") or [data]
    return list(data)
