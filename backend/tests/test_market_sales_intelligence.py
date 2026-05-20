from app.intelligence.sales import (
    BuyerBehaviorEngine,
    LiquidityPressureEngine,
    MarketInsightEngine,
    PricePositioningEngine,
    SellingStrategyEngine,
)


def payloads():
    comparables = {
        "comparables_used": 8,
        "price_dispersion_index": 0.11,
        "market_distance": 0.22,
        "km_similarity": 82,
        "comparables": [
            {"price": 110000, "regional_similarity": 100},
            {"price": 112000, "regional_similarity": 100},
            {"price": 116000, "regional_similarity": 92},
            {"price": 118000, "regional_similarity": 100},
        ],
    }
    liquidity = {"demand_index": 74, "listing_volume": 8, "liquidity_level": "Alta"}
    confidence = {"confidence_score": 78}
    regional = {"regional_price_delta": 1.6, "regional_scope": "SP"}
    trends = {"trend_direction": "estável"}
    valuation = {"ideal_price": 116000, "market_reference": 115000}
    negotiation = {"recommended_price": 116000, "negotiation_floor": 112000, "negotiation_ceiling": 121000, "quick_sale_price": 111000}
    return valuation, negotiation, liquidity, confidence, comparables, regional, trends


def test_selling_strategy_is_derived_from_inputs():
    valuation, negotiation, liquidity, confidence, comparables, *_ = payloads()
    result = SellingStrategyEngine().analyze(valuation, negotiation, liquidity, confidence, comparables)
    assert result["recommended_listing_price"] >= result["safe_price_range"][0]
    assert result["quick_sale_price"] <= result["recommended_listing_price"]
    assert 0 <= result["overvaluation_risk"] <= 100
    assert result["recommended_adjustment"]


def test_price_positioning_percentile_and_pressure():
    valuation, _, liquidity, _, comparables, *_ = payloads()
    result = PricePositioningEngine().analyze(valuation, comparables, liquidity)
    assert 1 <= result["market_position_percentile"] <= 99
    assert result["competitiveness_level"]
    assert result["market_resistance"] in {"baixa", "moderada", "alta"}


def test_market_insight_and_pressure_are_consistent():
    valuation, negotiation, liquidity, confidence, comparables, regional, trends = payloads()
    strategy = SellingStrategyEngine().analyze(valuation, negotiation, liquidity, confidence, comparables)
    positioning = PricePositioningEngine().analyze(valuation, comparables, liquidity)
    pressure = LiquidityPressureEngine().analyze(liquidity, positioning, strategy, comparables)
    insight = MarketInsightEngine().analyze(comparables, liquidity, positioning, regional, trends, strategy)
    assert 0 <= pressure["pressure_score"] <= 100
    assert 12 <= pressure["sale_probability"] <= 95
    assert insight["executive_market_insight_v2"]
    assert insight["market_insight_bullets"]


def test_buyer_behavior_generates_non_generic_insights():
    class Vehicle:
        model = "tracker"
        state = "SP"

    valuation, _, liquidity, _, comparables, regional, _ = payloads()
    positioning = PricePositioningEngine().analyze(valuation, comparables, liquidity)
    result = BuyerBehaviorEngine().analyze(Vehicle(), comparables, liquidity, regional, positioning)
    assert result["buyer_behavior_insights"]
    assert result["buyer_price_sensitivity"] in {"alta", "média", "baixa"}
