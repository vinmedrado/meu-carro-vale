from comparables.comparable_intelligence_engine import ComparableIntelligenceEngine


def base_vehicle(**overrides):
    row = {
        "marca": "Toyota",
        "modelo": "Corolla",
        "versao": "XEI 2.0 Flex CVT",
        "ano": 2021,
        "km": 42000,
        "preco": 118000.0,
        "cidade": "São Paulo",
        "estado": "SP",
        "combustivel": "Flex",
        "cambio": "CVT",
        "qualidade_dado": 0.92,
        "fonte": "CSV",
        "url": "https://exemplo.com/base",
    }
    row.update(overrides)
    return row


def test_score_excelente_para_mesmo_modelo_ano_km_regiao():
    engine = ComparableIntelligenceEngine()
    target = base_vehicle()
    candidate = base_vehicle(preco=119500, km=45000, url="https://exemplo.com/1")
    result = engine.score(target, candidate)
    assert result["comparable_score"] >= 85
    assert result["match_quality"] == "Excelente"
    assert result["regional_match"] is True
    assert "mesma marca e modelo" in result["explanation"]


def test_score_reduzido_para_versao_e_regiao_diferentes():
    engine = ComparableIntelligenceEngine()
    target = base_vehicle()
    candidate = base_vehicle(versao="GLI 2.0", estado="RJ", cidade="Rio de Janeiro", km=90000, preco=108000, url="https://exemplo.com/2")
    result = engine.score(target, candidate)
    assert result["comparable_score"] < 85
    assert result["regional_match"] is False
    assert "peso regional menor" in result["explanation"]


def test_impacto_preco_para_cima_com_km_maior_e_preco_semelhante():
    engine = ComparableIntelligenceEngine()
    target = base_vehicle(preco=118000, km=40000)
    candidate = base_vehicle(preco=119000, km=65000, url="https://exemplo.com/3")
    result = engine.score(target, candidate)
    assert result["price_impact"] == "pressiona preço para cima"


def test_remove_outlier_e_retorna_estatisticas():
    engine = ComparableIntelligenceEngine(min_score=50)
    target = base_vehicle(preco=118000)
    candidates = [
        base_vehicle(preco=116000, km=41000, url="https://exemplo.com/a"),
        base_vehicle(preco=117500, km=43000, url="https://exemplo.com/b"),
        base_vehicle(preco=119000, km=44000, url="https://exemplo.com/c"),
        base_vehicle(preco=118500, km=39000, url="https://exemplo.com/d"),
        base_vehicle(preco=300000, km=42000, url="https://exemplo.com/outlier"),
    ]
    result = engine.find_comparables(target, candidates, limit=10)
    assert result["outliers_removed"] >= 1
    assert result["sample_statistics"]["quantidade_comparaveis"] == 4
    assert result["sample_statistics"]["preco_mediano"] > 0


def test_build_dataset_exporta_campos_necessarios():
    engine = ComparableIntelligenceEngine(min_score=50)
    records = [
        base_vehicle(url="https://exemplo.com/base", preco=118000),
        base_vehicle(url="https://exemplo.com/comp1", preco=119000, km=43000),
        base_vehicle(url="https://exemplo.com/comp2", preco=116000, km=50000),
    ]
    dataset = engine.build_dataset(records, limit_per_vehicle=2)
    assert dataset
    row = dataset[0]
    for field in ["vehicle_id", "comparable_id", "score", "match_quality", "price_delta", "km_delta", "year_delta", "regional_match", "explanation", "price_impact"]:
        assert field in row
