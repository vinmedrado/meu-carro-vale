import json
from pathlib import Path

import pandas as pd

from app.data_engine_bridge import DataEngineExportLoader, DataEngineValuationAdapter
from app.services.valuation_engine import ValuationInput


def write_exports(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([
        {"vehicle_id":"v1","comparable_id":"c1","marca":"Chevrolet","modelo":"Tracker","versao":"Premier","ano":2023,"estado":"SP","cidade":"Santo Andre","preco_base":118900,"preco_comparavel":116500,"km_base":32000,"km_comparavel":41000,"score":94,"comparable_score":94,"match_quality":"Excelente","price_delta":-2400,"km_delta":9000,"year_delta":0,"regional_match":True,"explanation":"Mesmo modelo e região compatível.","price_impact":"neutro","fonte":"csv","url":"https://exemplo.com/1"},
        {"vehicle_id":"v1","comparable_id":"c2","marca":"Chevrolet","modelo":"Tracker","versao":"Premier","ano":2023,"estado":"SP","cidade":"Sao Paulo","preco_base":118900,"preco_comparavel":118900,"km_base":32000,"km_comparavel":36000,"score":96,"comparable_score":96,"match_quality":"Excelente","price_delta":0,"km_delta":4000,"year_delta":0,"regional_match":True,"explanation":"Mesmo modelo, km próxima e estado compatível.","price_impact":"neutro","fonte":"csv","url":"https://exemplo.com/2"},
    ]).to_csv(root / "comparables.csv", index=False)
    pd.DataFrame([{"marca":"Chevrolet","modelo":"Tracker","ano":2023,"regiao":"SP","qtd_anuncios":8,"dispersao_preco":0.08,"saturacao":0.12,"pressao_mercado":0.18,"volume_regional":0.7,"estabilidade":0.86,"velocidade_venda_estimada":"18 a 28 dias","tendencia":"estável","temperatura_mercado":"Aquecido","liquidity_level":"Alta"}]).to_csv(root / "liquidity.csv", index=False)
    pd.DataFrame([{"brand":"Chevrolet","model":"Tracker","version":"Premier","year":2023,"state":"SP","city":"Santo Andre","pressure_level":"Pressão moderada","velocity_level":"Boa velocidade","resistance_price":123500,"trend_direction":"Estável","stuck_risk_level":"Baixo","regional_strength":"Forte","summary":"Mercado com boa leitura regional e faixa competitiva."}]).to_csv(root / "market_behavior.csv", index=False)
    pd.DataFrame([{"marca":"Chevrolet","modelo":"Tracker","versao":"Premier","ano":2023,"regiao":"SP","estado":"SP","cidade":"Santo Andre","semana":21,"mes":"2026-05","qtd_anuncios":8,"preco_medio":117500,"preco_mediano":117000,"preco_p10":113000,"preco_p25":115000,"preco_p75":119000,"preco_p90":122000,"dispersao_preco":0.08,"liquidez":"Alta","temperatura_mercado":"Aquecido"}]).to_csv(root / "snapshots.csv", index=False)
    (root / "manifest.json").write_text(json.dumps({"generated_at":"2026-05-19T10:00:00Z","schema_registry_version":"1.0.0","validation_status":"aprovado","quality_score":0.96}), encoding="utf-8")


def test_loader_validates_contracts(tmp_path):
    write_exports(tmp_path)
    result = DataEngineExportLoader(tmp_path).validate_exports()
    assert result.available is True
    assert result.files["comparables"]["records"] == 2


def test_adapter_generates_data_engine_valuation(tmp_path):
    write_exports(tmp_path)
    vehicle = ValuationInput(
        brand="Chevrolet", model="Tracker", version="Premier", year=2023, km=32000,
        transmission="automático", fuel="flex", color="prata", options="", condition="bom", state="SP", city="Santo Andre",
    )
    payload = DataEngineValuationAdapter(DataEngineExportLoader(tmp_path)).evaluate(vehicle)
    assert payload is not None
    assert payload["data_engine_exports_used"] is True
    assert payload["mode"] == "DATA_ENGINE_EXPORTS"
    assert payload["ideal_price"] == 117000
    assert payload["comparables"]
    assert payload["selling_decision"]["seller_summary"]
