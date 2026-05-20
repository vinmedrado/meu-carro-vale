from jobs.pipeline import MCVDataPipeline


def test_pipeline_process_records(tmp_path):
    rows = [
        {"marca": "Jeep", "modelo": "Compass", "versao": "Longitude", "ano": 2022, "km": 40000, "preco": 145000, "cidade": "São Paulo", "estado": "SP", "fonte": "CSV"},
        {"marca": "Jeep", "modelo": "Compass", "versao": "Longitude", "ano": 2022, "km": 42000, "preco": 148000, "cidade": "Campinas", "estado": "SP", "fonte": "CSV"},
        {"marca": "Jeep", "modelo": "Compass", "versao": "Longitude", "ano": 2022, "km": 41000, "preco": 147000, "cidade": "Santos", "estado": "SP", "fonte": "CSV"},
    ]
    result = MCVDataPipeline(export_dir=tmp_path).process_records(rows)
    assert result["received"] == 3
    assert result["clean_records"] == 3
    assert result["snapshots"] == 1
    assert result["liquidity_rows"] == 1
    assert "market_listings" in result["exports"]
