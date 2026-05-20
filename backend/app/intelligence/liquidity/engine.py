from __future__ import annotations

import statistics
from typing import Any


class LiquidityEngine:
    def analyze(self, comparables_payload: dict[str, Any]) -> dict[str, Any]:
        comparables = comparables_payload.get("comparables", [])
        prices = [float(item.get("price", 0)) for item in comparables if item.get("price")]
        volume = len(prices)
        regional_volume = len([item for item in comparables if item.get("regional_similarity", 0) >= 95])
        dispersion = comparables_payload.get("price_dispersion_index", 0.55)
        if not dispersion and len(prices) > 1 and statistics.median(prices):
            dispersion = statistics.pstdev(prices) / statistics.median(prices)
        demand_index = int(max(15, min(100, 35 + volume * 3.2 + regional_volume * 2.3 - dispersion * 42)))
        sale_velocity = "rápida" if demand_index >= 78 else "normal" if demand_index >= 55 else "lenta"
        level = "Muito Alta" if demand_index >= 84 else "Alta" if demand_index >= 68 else "Média" if demand_index >= 48 else "Baixa"
        return {
            "liquidity_level": level,
            "market_temperature": "Aquecido" if demand_index >= 74 else "Equilibrado" if demand_index >= 52 else "Frio",
            "sale_velocity": sale_velocity,
            "demand_index": demand_index,
            "listing_volume": volume,
            "regional_volume": regional_volume,
            "saturation": "alta" if volume > 25 and demand_index < 60 else "controlada",
            "average_days_on_market_estimate": max(18, min(95, int(88 - demand_index * .7 + dispersion * 20))),
        }
