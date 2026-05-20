from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.intelligence.comparables.engine import ComparableEngine
from app.intelligence.confidence.engine import ConfidenceEngine
from app.intelligence.liquidity.engine import LiquidityEngine
from app.intelligence.negotiation.engine import NegotiationEngine
from app.intelligence.regional.engine import RegionalEngine
from app.intelligence.trends.engine import MarketTrendEngine
from app.intelligence.explainability.engine import ExplainableValuationEngine
from app.intelligence.sales import (
    BuyerBehaviorEngine,
    LiquidityPressureEngine,
    MarketInsightEngine,
    PricePositioningEngine,
    SellingStrategyEngine,
    SellingDecisionEngine,
)
from app.intelligence.normalization.vehicle import normalize_vehicle_query
from app.models.market import ComparableVehicle, MarketTrend, NegotiationRange, RegionalValuation, ValuationConfidence


class MCVIntelligenceEngine:
    """Orquestrador da camada MCV Intelligence Engine.

    Mantém o valuation atual como base e adiciona explicabilidade, comparáveis,
    liquidez, negociação, regionalização e tendência sem quebrar contratos antigos.
    """

    def __init__(self) -> None:
        self.comparables = ComparableEngine()
        self.liquidity = LiquidityEngine()
        self.negotiation = NegotiationEngine()
        self.confidence = ConfidenceEngine()
        self.regional = RegionalEngine()
        self.trends = MarketTrendEngine()
        self.explainability = ExplainableValuationEngine()
        self.selling_strategy = SellingStrategyEngine()
        self.price_positioning = PricePositioningEngine()
        self.buyer_behavior = BuyerBehaviorEngine()
        self.market_insights = MarketInsightEngine()
        self.liquidity_pressure = LiquidityPressureEngine()
        self.selling_decision = SellingDecisionEngine()

    def enrich(self, db: Session, vehicle: Any, valuation: dict[str, Any]) -> dict[str, Any]:
        comparable_payload = self.comparables.analyze(db, vehicle)
        liquidity_payload = self.liquidity.analyze(comparable_payload)
        confidence_payload = self.confidence.analyze(comparable_payload, liquidity_payload, valuation)
        regional_payload = self.regional.analyze(getattr(vehicle, "state", ""), comparable_payload, liquidity_payload)
        trend_payload = self.trends.analyze(comparable_payload, liquidity_payload)
        negotiation_payload = self.negotiation.analyze({**valuation, **confidence_payload}, liquidity_payload, comparable_payload)
        selling_strategy_payload = self.selling_strategy.analyze(valuation, negotiation_payload, liquidity_payload, confidence_payload, comparable_payload)
        price_positioning_payload = self.price_positioning.analyze({**valuation, **negotiation_payload}, comparable_payload, liquidity_payload)
        buyer_behavior_payload = self.buyer_behavior.analyze(vehicle, comparable_payload, liquidity_payload, regional_payload, price_positioning_payload)
        liquidity_pressure_payload = self.liquidity_pressure.analyze(liquidity_payload, price_positioning_payload, selling_strategy_payload, comparable_payload)
        market_insight_payload = self.market_insights.analyze(comparable_payload, liquidity_payload, price_positioning_payload, regional_payload, trend_payload, selling_strategy_payload)
        selling_decision_payload = self.selling_decision.analyze(valuation, negotiation_payload, liquidity_payload, confidence_payload, comparable_payload, price_positioning_payload, buyer_behavior_payload)
        liquidity_payload = {**liquidity_payload, **liquidity_pressure_payload}
        negotiation_payload = {**negotiation_payload, **selling_strategy_payload}
        explainability_payload = self.explainability.analyze(vehicle, valuation, comparable_payload, liquidity_payload, confidence_payload, regional_payload, trend_payload, negotiation_payload)
        explainability_payload = self._extend_explainability(explainability_payload, valuation, liquidity_payload, regional_payload, price_positioning_payload, buyer_behavior_payload, selling_strategy_payload)

        existing_comparables = valuation.get("comparables") or []
        intelligence_comparables = comparable_payload.get("comparables") or []
        if not existing_comparables and intelligence_comparables:
            valuation["comparables"] = [
                {
                    "id": item.get("listing_id"),
                    "title": item.get("title"),
                    "price": int(round(float(item.get("price") or 0) / 100) * 100),
                    "year": item.get("year"),
                    "mileage": item.get("mileage"),
                    "city": item.get("city"),
                    "state": item.get("state"),
                    "source": item.get("source"),
                    "similarity_score": item.get("similarity_score"),
                }
                for item in intelligence_comparables[:12]
            ]

        valuation.update(
            {
                "mcv_intelligence_version": "1.0",
                "mcv_intelligence": {
                    "comparables": comparable_payload,
                    "liquidity": liquidity_payload,
                    "negotiation": negotiation_payload,
                    "confidence": confidence_payload,
                    "regional": regional_payload,
                    "trends": trend_payload,
                    "explainability": explainability_payload,
                    "selling_strategy": selling_strategy_payload,
                    "price_positioning": price_positioning_payload,
                    "buyer_behavior": buyer_behavior_payload,
                    "market_insights": market_insight_payload,
                    "liquidity_pressure": liquidity_pressure_payload,
                    "selling_decision": selling_decision_payload,
                    "methodology": [
                        "normalização de marca, modelo, versão, ano, km e região",
                        "ranking de comparáveis por similaridade e distância de mercado",
                        "remoção estatística de outliers por intervalo interquartil",
                        "faixa de negociação ajustada por demanda, liquidez e confiança",
                        "explicabilidade por qualidade da amostra, dispersão e aderência regional",
                        "estratégia comercial por liquidez, pressão de preço e comportamento comprador",
                        "semáforo de negociação por faixa recomendada, menor valor e pressão de liquidez",
                    ],
                },
                "comparables_used": comparable_payload["comparables_used"],
                "similarity_score": comparable_payload["similarity_score"],
                "regional_similarity": comparable_payload["regional_similarity"],
                "km_similarity": comparable_payload["km_similarity"],
                "market_distance": comparable_payload["market_distance"],
                "outliers_removed": comparable_payload["outliers_removed"],
                "liquidity_level": liquidity_payload["liquidity_level"],
                "market_temperature": liquidity_payload["market_temperature"],
                "sale_velocity": liquidity_payload["sale_velocity"],
                "demand_index": liquidity_payload["demand_index"],
                "recommended_price": negotiation_payload["recommended_price"],
                "negotiation_ceiling": negotiation_payload["negotiation_ceiling"],
                "negotiation_floor": negotiation_payload["negotiation_floor"],
                "estimated_negotiation_margin": negotiation_payload["estimated_negotiation_margin"],
                "confidence_level": confidence_payload["confidence_level"],
                "confidence_score": max(int(valuation.get("confidence_score") or 0), confidence_payload["confidence_score"]),
                "confidence_reason": confidence_payload["confidence_reason"],
                "analysis_quality": confidence_payload["analysis_quality"],
                "regional_multiplier": regional_payload["regional_multiplier"],
                "regional_market_temperature": regional_payload["regional_market_temperature"],
                "regional_price_delta": regional_payload["regional_price_delta"],
                "trend_direction": trend_payload["trend_direction"],
                "weekly_trend": trend_payload["weekly_trend"],
                "monthly_trend": trend_payload["monthly_trend"],
                "valuation_explanation": explainability_payload["valuation_explanation"],
                "valuation_explanation_text": explainability_payload["valuation_explanation_text"],
                "positive_impact_total": explainability_payload["positive_impact_total"],
                "negative_impact_total": explainability_payload["negative_impact_total"],
                "comparable_analysis": explainability_payload["comparable_analysis"],
                "executive_market_insight": explainability_payload["executive_market_insight"],
                "market_temperature_detail": explainability_payload["market_temperature_detail"],
                "regional_explanation": explainability_payload["regional_explanation"],
                "negotiation_intelligence": {**explainability_payload["negotiation_intelligence"], **selling_strategy_payload},
                "selling_strategy": selling_strategy_payload,
                "price_positioning": price_positioning_payload,
                "buyer_behavior": buyer_behavior_payload,
                "market_insights": market_insight_payload,
                "liquidity_pressure": liquidity_pressure_payload,
                "market_position_percentile": price_positioning_payload["market_position_percentile"],
                "competitiveness_level": price_positioning_payload["competitiveness_level"],
                "pricing_pressure": price_positioning_payload["pricing_pressure"],
                "market_resistance": price_positioning_payload["market_resistance"],
                "pressure_score": liquidity_pressure_payload["pressure_score"],
                "sale_probability": liquidity_pressure_payload["sale_probability"],
                "estimated_market_resistance": liquidity_pressure_payload["estimated_market_resistance"],
                "market_temperature_label": market_insight_payload["market_temperature_label"],
                "market_temperature_score": market_insight_payload["market_temperature_score"],
                "executive_market_insight_v2": market_insight_payload["executive_market_insight_v2"],
                "market_insight_bullets": market_insight_payload["market_insight_bullets"],
                "buyer_behavior_insights": buyer_behavior_payload["buyer_behavior_insights"],
                "buyer_price_sensitivity": buyer_behavior_payload["buyer_price_sensitivity"],
                "recommended_listing_price": selling_strategy_payload["recommended_listing_price"],
                "safe_price_range": selling_strategy_payload["safe_price_range"],
                "probable_ceiling": selling_strategy_payload["probable_ceiling"],
                "overvaluation_risk": selling_strategy_payload["overvaluation_risk"],
                "recommended_adjustment": selling_strategy_payload["recommended_adjustment"],
                "selling_decision": selling_decision_payload,
                "listing_price": selling_decision_payload["listing_price"],
                "ideal_close_range_min": selling_decision_payload["ideal_close_range_min"],
                "ideal_close_range_max": selling_decision_payload["ideal_close_range_max"],
                "minimum_recommended_price": selling_decision_payload["minimum_recommended_price"],
                "resistance_price": selling_decision_payload["resistance_price"],
                "stuck_risk_level": selling_decision_payload["stuck_risk_level"],
                "stuck_risk_reason": selling_decision_payload["stuck_risk_reason"],
                "review_price_after_days": selling_decision_payload["review_price_after_days"],
                "suggested_price_cut_percent": selling_decision_payload["suggested_price_cut_percent"],
                "negotiation_signal": selling_decision_payload["negotiation_signal"],
                "negotiation_message": selling_decision_payload["negotiation_message"],
                "price_defense_arguments": selling_decision_payload["price_defense_arguments"],
                "seller_summary": selling_decision_payload["seller_summary"],
                "psychological_price_note": selling_decision_payload["psychological_price_note"],
            }
        )
        valuation["negotiation_range"] = [negotiation_payload["negotiation_floor"], negotiation_payload["negotiation_ceiling"]]
        valuation["quick_sale_price"] = negotiation_payload["quick_sale_price"] or valuation.get("quick_sale_price")
        valuation["ideal_price"] = negotiation_payload["recommended_price"] or valuation.get("ideal_price")
        self._persist(db, vehicle, comparable_payload, liquidity_payload, confidence_payload, regional_payload, trend_payload, negotiation_payload)
        return valuation

    def _extend_explainability(self, explainability: dict[str, Any], valuation: dict[str, Any], liquidity: dict[str, Any], regional: dict[str, Any], positioning: dict[str, Any], buyer_behavior: dict[str, Any], strategy: dict[str, Any]) -> dict[str, Any]:
        base = float(valuation.get("ideal_price") or valuation.get("market_reference") or 0)
        factors = list(explainability.get("valuation_explanation") or [])
        demand = int(liquidity.get("demand_index") or 50)
        regional_delta = float(regional.get("regional_price_delta") or 0)
        pressure = int(liquidity.get("pressure_score") or 0)
        percentile = int(positioning.get("market_position_percentile") or 50)
        sensitivity = str(buyer_behavior.get("buyer_price_sensitivity") or "média")

        def add(label: str, value: float, weight: int, reason: str) -> None:
            factors.append({
                "factor": label,
                "impact_value": int(round(value / 100) * 100),
                "impact_direction": "positivo" if value > 0 else "negativo" if value < 0 else "neutro",
                "weight": weight,
                "reason": reason,
            })

        if base:
            if demand >= 70:
                add("Liquidez comercial", base * min(.026, (demand - 62) / 1200), 14, "facilidade esperada de venda acima da média")
            elif demand < 48:
                add("Liquidez comercial", -base * min(.024, (50 - demand) / 1100), 14, "mercado mais lento para o recorte analisado")
            if abs(regional_delta) >= .8:
                add("Prêmio regional" if regional_delta > 0 else "Ajuste regional", base * (regional_delta / 100), 12, "diferença regional observada na amostra")
            if pressure >= 65:
                add("Pressão de mercado", -base * min(.028, pressure / 3600), 11, "resistência esperada para anúncios no topo da faixa")
            elif pressure <= 35:
                add("Pressão de mercado", base * .008, 8, "baixa resistência para preços dentro da faixa segura")
            if percentile >= 75:
                add("Posicionamento competitivo", -base * .012, 9, "preço acima da maioria dos comparáveis exige prova de valor")
            elif percentile <= 40:
                add("Posicionamento competitivo", base * .01, 9, "preço competitivo frente aos comparáveis")
            if sensitivity == "alta":
                add("Comportamento comprador", -base * .009, 7, "compradores devem demonstrar maior sensibilidade a preço")
            elif sensitivity == "baixa":
                add("Comportamento comprador", base * .006, 6, "baixa sensibilidade de preço dentro da faixa sugerida")

        explainability["valuation_explanation"] = factors
        explainability["positive_impact_total"] = int(sum(float(x.get("impact_value") or 0) for x in factors if float(x.get("impact_value") or 0) > 0))
        explainability["negative_impact_total"] = int(sum(float(x.get("impact_value") or 0) for x in factors if float(x.get("impact_value") or 0) < 0))
        explainability["valuation_explanation_text"] = self._consultative_summary(factors, strategy, positioning, liquidity)
        return explainability

    def _consultative_summary(self, factors: list[dict[str, Any]], strategy: dict[str, Any], positioning: dict[str, Any], liquidity: dict[str, Any]) -> str:
        relevant = sorted(factors, key=lambda item: abs(float(item.get("impact_value") or 0)), reverse=True)[:4]
        fragments = []
        for item in relevant:
            value = abs(int(item.get("impact_value") or 0))
            signal = "+" if item.get("impact_direction") == "positivo" else "-" if item.get("impact_direction") == "negativo" else ""
            if value:
                fragments.append(f"{signal}R$ {value:,.0f}".replace(",", ".") + f" por {item.get('reason')}")
        base = "; ".join(fragments) if fragments else "a faixa foi mantida por equilíbrio entre comparáveis e referência técnica"
        return f"A recomendação combina evidência de mercado, liquidez e comportamento comprador: {base}. Estratégia indicada: {strategy.get('strategy_label', 'equilíbrio comercial')}; posição competitiva: {positioning.get('competitiveness_level', 'em análise')}; demanda {liquidity.get('demand_index', 0)}/100."

    def _persist(self, db: Session, vehicle: Any, comparables: dict[str, Any], liquidity: dict[str, Any], confidence: dict[str, Any], regional: dict[str, Any], trends: dict[str, Any], negotiation: dict[str, Any]) -> None:
        query = normalize_vehicle_query(vehicle)
        try:
            for item in (comparables.get("comparables") or [])[:12]:
                db.add(ComparableVehicle(
                    market_listing_id=item.get("listing_id"), brand=query.brand, model=query.model, version=query.version,
                    year=query.year, mileage=query.mileage, state=query.state, source=item.get("source") or "",
                    price=float(item.get("price") or 0), similarity_score=int(item.get("similarity_score") or 0),
                    regional_similarity=int(item.get("regional_similarity") or 0), km_similarity=int(item.get("km_similarity") or 0),
                    market_distance=float(item.get("market_distance") or 0), payload=item,
                ))
            db.add(ValuationConfidence(
                confidence_score=int(confidence.get("confidence_score") or 0),
                confidence_level=str(confidence.get("confidence_level") or "Baixa"),
                confidence_reason=str(confidence.get("confidence_reason") or ""),
                analysis_quality=str(confidence.get("analysis_quality") or "exploratória"),
                comparable_count=int(comparables.get("comparables_used") or 0),
                dispersion=float(comparables.get("price_dispersion_index") or 0),
                payload={"comparables": comparables, "liquidity": liquidity, "confidence": confidence},
            ))
            db.add(NegotiationRange(
                quick_sale_price=float(negotiation.get("quick_sale_price") or 0),
                recommended_price=float(negotiation.get("recommended_price") or 0),
                negotiation_floor=float(negotiation.get("negotiation_floor") or 0),
                negotiation_ceiling=float(negotiation.get("negotiation_ceiling") or 0),
                estimated_negotiation_margin=float(negotiation.get("estimated_negotiation_margin") or 0),
                positioning=str(negotiation.get("positioning") or "equilibrado"),
                payload=negotiation,
            ))
            db.add(RegionalValuation(
                brand=query.brand, model=query.model, year=query.year, state=query.state,
                regional_multiplier=float(regional.get("regional_multiplier") or 1),
                regional_market_temperature=str(regional.get("regional_market_temperature") or "Equilibrado"),
                regional_price_delta=float(regional.get("regional_price_delta") or 0),
                sample_size=int(comparables.get("comparables_used") or 0),
                payload=regional,
            ))
            db.add(MarketTrend(
                brand=query.brand, model=query.model, year=query.year, state=query.state,
                trend_direction=str(trends.get("trend_direction") or "estável"),
                weekly_trend=str(trends.get("weekly_trend") or "monitorar"),
                monthly_trend=str(trends.get("monthly_trend") or "monitorar"),
                price_spread=float(trends.get("price_spread") or 0),
                payload=trends,
            ))
            db.commit()
        except Exception:
            db.rollback()
