from pathlib import Path

from ingestion.csv_ingestion.csv_ingestor import CSVIngestor
from jobs.pipeline import MCVDataPipeline


def test_csv_ingestion_chunked(tmp_path: Path):
    csv_path = tmp_path / "listings.csv"
    csv_path.write_text("marca,modelo,ano,km,preco,cidade,estado,fonte\nToyota,Corolla,2020,40000,115000,São Paulo,SP,CSV\n", encoding="utf-8")
    rows = CSVIngestor(chunk_size=1).ingest(csv_path)
    assert len(rows) == 1
    assert rows[0]["normalization_status"].startswith("normalizado")


def test_pipeline_generates_quality_and_comparables(tmp_path: Path):
    csv_path = tmp_path / "listings.csv"
    csv_path.write_text("marca,modelo,versao,ano,km,preco,cidade,estado,fonte,url\nToyota,Corolla,XEI,2020,40000,115000,São Paulo,SP,CSV,http://a\nToyota,Corolla,XEI,2020,41000,116000,São Paulo,SP,CSV,http://b\n", encoding="utf-8")
    result = MCVDataPipeline(export_dir=tmp_path / "exports").run_import(csv_path)
    assert result["received"] == 2
    assert result["quality_rows"] >= 1
    assert result["comparables_rows"] >= 1
