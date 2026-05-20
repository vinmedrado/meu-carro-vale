from app.market_intelligence.normalizers.vehicle_normalizer import normalize_listing, normalize_brand, normalize_transmission
from app.market_intelligence.analytics.outliers import remove_price_outliers
from app.market_intelligence.deduplication.deduplicator import duplicate_score
from app.market_intelligence.liquidity.liquidity_engine import LiquidityEngine


def test_normalization_aliases():
    row = normalize_listing({"titulo":"VW Polo Highline 2020", "preco":"R$ 78.900", "marca":"VW", "modelo":"Polo 1.0 Turbo", "ano":"2020", "km":"45.000", "uf":"sp", "cambio":"aut"}, source="csv")
    assert row.brand == "volkswagen"
    assert row.model == "polo"
    assert row.transmission == "automático"
    assert row.price == 78900


def test_outlier_filter_removes_absurd_price():
    values = [70000, 72000, 73000, 74000, 75000, 76000, 900000]
    filtered = remove_price_outliers(values)
    assert 900000 not in filtered


def test_duplicate_score_detects_repost():
    left = {"title":"Honda Civic EXL 2021", "price":125000, "mileage":41000, "brand":"honda", "model":"civic", "year":2021, "state":"SP"}
    right = {"title":"Honda Civic EXL 2021 impecável", "price":126000, "mileage":41200, "brand":"honda", "model":"civic", "year":2021, "state":"SP"}
    assert duplicate_score(left, right).duplicate_score >= 75


def test_liquidity_labels():
    result = LiquidityEngine().calculate([100000, 101000, 99000, 100500, 99800, 101200, 99700, 100300, 100100, 99900], regional_count=8)
    assert result.score >= 60
    assert result.label in {"Alta", "Muito Alta", "Média"}

from app.services.valuation_engine import ValuationEngine, ValuationInput


def test_demo_valuation_transparency_payload():
    vehicle = ValuationInput(
        brand="Toyota", model="Corolla", version="XEi", year=2021, km=62000,
        transmission="automático", fuel="flex", color="prata", options="multimidia,couro",
        condition="bom", state="SP", city="São Paulo",
    )
    result = ValuationEngine().evaluate(vehicle)
    assert result["valuation_explanation"]
    assert result["methodology_summary"]
    assert result["confidence_explanation"]
    assert result["liquidity_explanation"]
    assert result["comparables_used"] > 0
    assert result["price_dispersion"]["p25"] <= result["price_dispersion"]["p50"] <= result["price_dispersion"]["p75"]
    assert result["market_snapshot"]["status"]
    assert result["real_market_weight"] > result["fipe_weight"]
