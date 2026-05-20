from __future__ import annotations

from typing import Any


def _round_money(value: float) -> int:
    return int(round(value / 100) * 100)


class NegotiationEngine:
    def analyze(self, base_valuation: dict[str, Any], liquidity: dict[str, Any], comparables: dict[str, Any]) -> dict[str, Any]:
        ideal = float(base_valuation.get("ideal_price") or base_valuation.get("market_reference") or 0)
        p = comparables.get("percentiles", {})
        p25 = float(p.get("p25") or ideal * .94)
        p75 = float(p.get("p75") or ideal * 1.06)
        confidence = int(base_valuation.get("confidence_score") or 55)
        demand = int(liquidity.get("demand_index") or 50)
        quick_factor = .93 if demand < 50 else .95 if demand < 75 else .965
        ceiling_factor = 1.055 if confidence >= 75 else 1.035
        floor = min(p25, ideal * .94)
        recommended = max(min(ideal, p75), floor)
        ceiling = max(p75, recommended * ceiling_factor)
        return {
            "quick_sale_price": _round_money(recommended * quick_factor),
            "recommended_price": _round_money(recommended),
            "negotiation_ceiling": _round_money(ceiling),
            "negotiation_floor": _round_money(floor),
            "estimated_negotiation_margin": round(((ceiling - floor) / recommended) * 100, 1) if recommended else 0,
            "positioning": "defensivo" if demand < 50 else "equilibrado" if demand < 78 else "valorizado",
        }
