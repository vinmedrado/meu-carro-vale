from __future__ import annotations

from typing import Any

from .utils import clamp, money


class SellingStrategyEngine:
    """Define uma estratégia de anúncio e negociação a partir da faixa calculada."""

    def analyze(self, valuation: dict[str, Any], negotiation: dict[str, Any], liquidity: dict[str, Any], confidence: dict[str, Any], comparables: dict[str, Any]) -> dict[str, Any]:
        ideal = float(negotiation.get("recommended_price") or valuation.get("ideal_price") or valuation.get("market_reference") or 0)
        floor = float(negotiation.get("negotiation_floor") or valuation.get("quick_sale_price") or ideal * .94)
        ceiling = float(negotiation.get("negotiation_ceiling") or valuation.get("recommended_top_price") or ideal * 1.06)
        demand = int(liquidity.get("demand_index") or 50)
        confidence_score = int(confidence.get("confidence_score") or valuation.get("confidence_score") or 55)
        dispersion = float(comparables.get("price_dispersion_index") or 0)
        pressure = float(comparables.get("market_distance") or 0)

        opening_multiplier = 1.018 if demand >= 75 and confidence_score >= 68 else 1.01 if demand >= 55 else .998
        best_initial = money(clamp(ideal * opening_multiplier, floor, max(ceiling, ideal)))
        quick_sale = money(float(negotiation.get("quick_sale_price") or ideal * (.94 if demand < 60 else .965)))
        safe_low = money(max(floor, ideal * (.965 if demand >= 65 else .945)))
        safe_high = money(min(max(ceiling, safe_low), ideal * (1.055 if confidence_score >= 72 else 1.035)))
        probable_ceiling = money(max(ceiling, best_initial * (1.018 if demand >= 75 else 1.01)))
        overvaluation_risk = int(clamp(30 + dispersion * 125 + max(0, 60 - demand) * .8 + pressure * 28, 8, 96))
        adjustment = "manter preço por 10 a 14 dias" if demand >= 72 and overvaluation_risk < 55 else "testar preço por 7 dias e reduzir se houver baixa procura" if demand >= 52 else "entrar competitivo desde o primeiro anúncio"
        resistance_price = money(probable_ceiling * (1.005 if demand >= 70 else .992))

        return {
            "recommended_listing_price": best_initial,
            "safe_price_range": [safe_low, safe_high],
            "quick_sale_price": quick_sale,
            "probable_ceiling": probable_ceiling,
            "overvaluation_risk": overvaluation_risk,
            "recommended_adjustment": adjustment,
            "resistance_price": resistance_price,
            "strategy_label": "valorizar com margem" if demand >= 76 else "equilíbrio comercial" if demand >= 52 else "liquidez primeiro",
            "strategy_reason": self._reason(demand, confidence_score, dispersion, overvaluation_risk),
        }

    def _reason(self, demand: int, confidence: int, dispersion: float, risk: int) -> str:
        parts: list[str] = []
        parts.append("demanda regional favorável" if demand >= 70 else "demanda em equilíbrio" if demand >= 52 else "demanda mais lenta")
        parts.append("amostra consistente" if confidence >= 70 else "amostra ainda moderada")
        parts.append("baixa dispersão" if dispersion <= .14 else "dispersão relevante")
        parts.append("baixo risco de supervalorização" if risk < 45 else "risco moderado de resistência" if risk < 70 else "alto risco de resistência")
        return ", ".join(parts) + "."
