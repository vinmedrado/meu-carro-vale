from __future__ import annotations

from typing import Any

from .utils import clamp, percentile_rank, prices_from, pct


class PricePositioningEngine:
    """Lê a posição competitiva do preço frente aos comparáveis usados."""

    def analyze(self, valuation: dict[str, Any], comparables: dict[str, Any], liquidity: dict[str, Any]) -> dict[str, Any]:
        prices = prices_from(comparables)
        ideal = float(valuation.get("ideal_price") or valuation.get("recommended_price") or valuation.get("market_reference") or 0)
        percentile = percentile_rank(ideal, prices)
        dispersion = float(comparables.get("price_dispersion_index") or 0)
        demand = int(liquidity.get("demand_index") or 50)
        pressure_score = int(clamp((percentile - 50) * 1.05 + dispersion * 90 + max(0, 56 - demand), 0, 100))

        if percentile >= 78:
            competitiveness = "acima da maioria dos anúncios"
        elif percentile >= 58:
            competitiveness = "ligeiramente acima da média"
        elif percentile >= 36:
            competitiveness = "competitivo"
        else:
            competitiveness = "agressivo para venda"

        resistance = "alta" if pressure_score >= 72 else "moderada" if pressure_score >= 46 else "baixa"
        pricing_pressure = "forte" if percentile >= 76 and demand < 65 else "controlada" if demand >= 55 else "sensível"
        return {
            "market_position_percentile": percentile,
            "competitiveness_level": competitiveness,
            "pricing_pressure": pricing_pressure,
            "market_resistance": resistance,
            "positioning_score": 100 - pressure_score,
            "positioning_summary": f"O valor indicado fica acima de {percentile}% dos anúncios comparáveis." if prices else "Sem amostra suficiente para percentil competitivo.",
            "dispersion_used": pct(dispersion * 100),
        }
