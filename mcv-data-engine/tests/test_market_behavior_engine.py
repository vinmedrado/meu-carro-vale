from market_behavior.market_behavior_engine import MarketBehaviorEngine
from market_behavior.price_pressure_engine import PricePressureEngine
from market_behavior.market_velocity_engine import MarketVelocityEngine
from market_behavior.resistance_engine import ResistanceEngine
from market_behavior.regional_behavior_engine import RegionalBehaviorEngine
from market_behavior.trend_behavior_engine import TrendBehaviorEngine


def _comparables():
    return [
        {"marca": "Toyota", "modelo": "Corolla", "versao": "XEI", "ano": 2021, "km": 45000, "preco": 118000, "estado": "SP", "cidade": "Sao Paulo", "data_coleta": "2026-05-10", "comparable_score": 92},
        {"marca": "Toyota", "modelo": "Corolla", "versao": "XEI", "ano": 2021, "km": 52000, "preco": 116500, "estado": "SP", "cidade": "Sao Paulo", "data_coleta": "2026-05-11", "comparable_score": 89},
        {"marca": "Toyota", "modelo": "Corolla", "versao": "XEI", "ano": 2020, "km": 61000, "preco": 112000, "estado": "SP", "cidade": "Campinas", "data_coleta": "2026-04-25", "comparable_score": 81},
        {"marca": "Toyota", "modelo": "Corolla", "versao": "XEI", "ano": 2022, "km": 39000, "preco": 124000, "estado": "RJ", "cidade": "Rio de Janeiro", "data_coleta": "2026-03-01", "comparable_score": 75},
        {"marca": "Toyota", "modelo": "Corolla", "versao": "GLI", "ano": 2021, "km": 70000, "preco": 109000, "estado": "SP", "cidade": "Santos", "data_coleta": "2026-05-01", "comparable_score": 70},
        {"marca": "Toyota", "modelo": "Corolla", "versao": "XEI", "ano": 2021, "km": 47000, "preco": 119500, "estado": "MG", "cidade": "Belo Horizonte", "data_coleta": "2026-05-08", "comparable_score": 84},
    ]


def _snapshots():
    return [
        {"marca": "Toyota", "modelo": "Corolla", "ano": 2021, "estado": "SP", "mes": "2026-04", "qtd_anuncios": 12, "preco_mediano": 114000, "dispersao_preco": 0.12},
        {"marca": "Toyota", "modelo": "Corolla", "ano": 2021, "estado": "SP", "mes": "2026-05", "qtd_anuncios": 18, "preco_mediano": 117000, "dispersao_preco": 0.10},
    ]


def test_price_pressure_returns_level_and_reason():
    result = PricePressureEngine().analyze(_comparables(), target_price=121000)
    assert 0 <= result["price_pressure_score"] <= 1
    assert result["pressure_level"] in {"Pressão baixa", "Pressão moderada", "Pressão alta", "Mercado pressionado"}
    assert result["pressure_reason"]


def test_market_velocity_uses_recency_and_snapshots():
    result = MarketVelocityEngine().analyze(_comparables(), _snapshots())
    assert 0 <= result["market_velocity_score"] <= 1
    assert result["estimated_sale_window"]


def test_resistance_engine_calculates_stuck_risk():
    pressure = PricePressureEngine().analyze(_comparables(), target_price=122000)
    velocity = MarketVelocityEngine().analyze(_comparables(), _snapshots())
    result = ResistanceEngine().analyze(_comparables(), 122000, pressure["price_pressure_score"], velocity["market_velocity_score"])
    assert result["resistance_price"] is not None
    assert result["stuck_risk"] in {"Baixo", "Moderado", "Alto"}


def test_regional_behavior_detects_regional_sample():
    result = RegionalBehaviorEngine().analyze(_comparables(), state="SP", city="Sao Paulo")
    assert result["regional_liquidity_level"]
    assert "regional_price_delta" in result


def test_trend_behavior_uses_snapshots():
    result = TrendBehaviorEngine().analyze(_snapshots())
    assert result["trend_direction"] in {"Em valorização", "Estável", "Em queda", "Volátil"}
    assert result["median_price_change"] > 0


def test_market_behavior_summary_and_stuck_risk():
    target = {"marca": "Toyota", "modelo": "Corolla", "ano": 2021, "estado": "SP", "cidade": "Sao Paulo", "preco": 118900}
    result = MarketBehaviorEngine().analyze(_comparables(), _snapshots(), target)
    assert result["stuck_risk_level"] in {"Baixo", "Moderado", "Alto"}
    assert result["market_behavior_summary"]
