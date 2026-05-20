from __future__ import annotations

from typing import Any

REGIONAL_MULTIPLIER = {"SP": 1.025, "RJ": 1.012, "MG": 1.0, "PR": 1.004, "SC": 1.01, "RS": .992, "BA": .985, "PE": .982, "GO": 1.0, "DF": 1.015}


class RegionalEngine:
    def analyze(self, state: str, comparables: dict[str, Any], liquidity: dict[str, Any]) -> dict[str, Any]:
        uf = str(state or "").upper()[:2]
        multiplier = REGIONAL_MULTIPLIER.get(uf, 1.0)
        regional_similarity = float(comparables.get("regional_similarity") or 0)
        temperature = liquidity.get("market_temperature", "Equilibrado")
        return {
            "regional_multiplier": multiplier,
            "regional_market_temperature": temperature,
            "regional_price_delta": round((multiplier - 1) * 100, 2),
            "regional_scope": uf or "BR",
            "regional_confidence": "alta" if regional_similarity >= 80 else "média" if regional_similarity >= 55 else "baixa",
        }
