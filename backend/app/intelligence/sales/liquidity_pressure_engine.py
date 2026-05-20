from __future__ import annotations

from typing import Any

from .utils import clamp


class LiquidityPressureEngine:
    """Amplia liquidez com pressão, probabilidade de venda e resistência estimada."""

    def analyze(self, liquidity: dict[str, Any], positioning: dict[str, Any], strategy: dict[str, Any], comparables: dict[str, Any]) -> dict[str, Any]:
        demand = int(liquidity.get("demand_index") or 50)
        resistance = str(positioning.get("market_resistance") or "moderada")
        percentile = int(positioning.get("market_position_percentile") or 50)
        dispersion = float(comparables.get("price_dispersion_index") or 0)
        pressure = int(clamp(100 - demand + max(0, percentile - 55) * .9 + dispersion * 80, 0, 100))
        probability = int(clamp(92 - pressure * .55 + max(0, demand - 60) * .25, 12, 95))
        if pressure >= 72:
            estimated_resistance = "forte resistência acima da faixa recomendada"
        elif pressure >= 48:
            estimated_resistance = "resistência moderada se o anúncio ficar no topo da faixa"
        else:
            estimated_resistance = "baixa resistência dentro da faixa segura"
        return {
            "pressure_score": pressure,
            "sale_probability": probability,
            "estimated_market_resistance": estimated_resistance,
            "resistance_price": strategy.get("resistance_price"),
            "liquidity_pressure_summary": f"Acima de R$ {int(strategy.get('resistance_price') or 0):,}".replace(',', '.') + f" o mercado tende a mostrar {resistance} resistência." if strategy.get("resistance_price") else estimated_resistance,
        }
