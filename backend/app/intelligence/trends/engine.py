from __future__ import annotations

from typing import Any


class MarketTrendEngine:
    def analyze(self, comparables: dict[str, Any], liquidity: dict[str, Any]) -> dict[str, Any]:
        p = comparables.get("percentiles", {})
        p25 = float(p.get("p25") or 0)
        p75 = float(p.get("p75") or 0)
        p50 = float(p.get("p50") or 0)
        spread = ((p75 - p25) / p50) if p50 else 0
        demand = int(liquidity.get("demand_index") or 50)
        direction = "alta" if demand >= 72 and spread < .18 else "queda" if demand < 42 else "estável"
        return {
            "trend_direction": direction,
            "weekly_trend": "monitorar" if direction == "estável" else direction,
            "monthly_trend": direction,
            "seasonality_note": "Base preparada para sazonalidade por histórico de snapshots.",
            "price_spread": round(spread, 3),
        }
