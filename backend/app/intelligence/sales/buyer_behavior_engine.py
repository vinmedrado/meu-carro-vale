from __future__ import annotations

from typing import Any


class BuyerBehaviorEngine:
    """Traduz sinais de mercado em leitura comercial sem inventar tendência externa."""

    def analyze(self, vehicle: Any, comparables: dict[str, Any], liquidity: dict[str, Any], regional: dict[str, Any], positioning: dict[str, Any]) -> dict[str, Any]:
        demand = int(liquidity.get("demand_index") or 50)
        km_similarity = float(comparables.get("km_similarity") or 0)
        regional_delta = float(regional.get("regional_price_delta") or 0)
        percentile = int(positioning.get("market_position_percentile") or 50)
        model = str(getattr(vehicle, "model", "veículo") or "veículo").title()
        state = str(getattr(vehicle, "state", "BR") or "BR").upper()

        insights: list[str] = []
        if km_similarity >= 78:
            insights.append("A quilometragem está bem alinhada ao que compradores comparam neste recorte.")
        elif km_similarity and km_similarity < 58:
            insights.append("A quilometragem tende a exigir argumentação mais clara no anúncio e na negociação.")
        if demand >= 70:
            insights.append(f"Há leitura de procura favorável para {model} na praça {state}.")
        elif demand < 48:
            insights.append(f"Compradores da praça {state} tendem a responder melhor a preços de entrada mais competitivos.")
        if regional_delta > 1.2:
            insights.append("A praça analisada mostra valorização regional acima da referência nacional.")
        elif regional_delta < -1.2:
            insights.append("A praça analisada pede cautela porque o recorte está abaixo da referência nacional.")
        if percentile >= 72:
            insights.append("Como o preço está no topo da amostra, a conservação e o histórico precisam sustentar a proposta.")
        elif percentile <= 38:
            insights.append("O preço tende a ser percebido como competitivo frente aos comparáveis.")
        if not insights:
            insights.append("O comportamento esperado é equilibrado: compradores devem comparar preço, quilometragem e histórico antes de avançar.")

        sensitivity = "alta" if percentile >= 72 or demand < 48 else "média" if percentile >= 55 else "baixa"
        return {
            "buyer_price_sensitivity": sensitivity,
            "km_sensitivity": "alta" if km_similarity < 58 else "moderada" if km_similarity < 76 else "baixa",
            "regional_buyer_profile": "valorização regional" if regional_delta > 1 else "negociação mais sensível" if regional_delta < -1 else "equilibrado",
            "buyer_behavior_insights": insights,
            "primary_buyer_argument": insights[0],
        }
