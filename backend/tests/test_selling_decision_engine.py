from app.intelligence.sales.selling_decision_engine import SellingDecisionEngine


def test_selling_decision_returns_consultative_fields():
    engine = SellingDecisionEngine()
    payload = engine.analyze(
        valuation={"ideal_price": 116000, "quick_sale_price": 109000, "confidence_score": 78},
        negotiation={"recommended_price": 116000, "quick_sale_price": 109000, "negotiation_floor": 112000, "negotiation_ceiling": 121000},
        liquidity={"demand_index": 74, "pressure_score": 42},
        confidence={"confidence_score": 78},
        comparables={"comparables_used": 12, "price_dispersion_index": 0.11},
        positioning={"market_position_percentile": 61},
        buyer_behavior={"km_sensitivity": "média"},
    )

    assert payload["listing_price"] > payload["ideal_close_range_min"]
    assert payload["minimum_recommended_price"] <= payload["ideal_close_range_min"]
    assert payload["resistance_price"] >= payload["ideal_close_range_max"]
    assert payload["stuck_risk_level"] in {"Baixo", "Moderado", "Alto"}
    assert payload["price_defense_arguments"]
    assert "Anuncie" in payload["seller_summary"]


def test_selling_decision_offer_semaphore():
    engine = SellingDecisionEngine()
    assert engine.classify_offer(114000, 118000, 112000, 115000)["signal"] == "Boa proposta"
    assert engine.classify_offer(114000, 118000, 112000, 112500)["signal"] == "Negociar com cuidado"
    assert engine.classify_offer(114000, 118000, 112000, 110000)["signal"] == "Proposta abaixo do recomendado"
