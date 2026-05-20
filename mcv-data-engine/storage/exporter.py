from __future__ import annotations
from pathlib import Path
import pandas as pd


class DatasetExporter:
    def __init__(self, output_dir: str | Path = "exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def export(self, name: str, records_or_df) -> dict[str, str]:
        df = records_or_df if isinstance(records_or_df, pd.DataFrame) else pd.DataFrame(records_or_df)
        paths: dict[str, str] = {}
        csv_path = self.output_dir / f"{name}.csv"
        df.to_csv(csv_path, index=False)
        paths["csv"] = str(csv_path)
        try:
            parquet_path = self.output_dir / f"{name}.parquet"
            df.to_parquet(parquet_path, index=False)
            paths["parquet"] = str(parquet_path)
        except Exception:
            paths["parquet"] = "parquet indisponível: instale pyarrow"
        return paths
