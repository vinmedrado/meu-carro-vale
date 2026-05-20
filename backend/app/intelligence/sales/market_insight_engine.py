from __future__ import annotations

from typing import Any


class MarketInsightEngine:
    """Gera síntese executiva baseada apenas nos sinais calculados pelo sistema."""

    def analyze(self, comparables: dict[str, Any], liquidity: dict[str, Any], positioning: dict[str, Any], regional: dict[str, Any], trends: dict[str, Any], strategy: dict[str, Any]) -> dict[str, Any]:
        demand = int(liquidity.get("demand_index") or 50)
        volume = int(liquidity.get("listing_volume") or comparables.get("comparables_used") or 0)
        dispersion = float(comparables.get("price_dispersion_index") or 0)
        trend = str(trends.get("trend_direction") or "estável")
        resistance = str(positioning.get("market_resistance") or "moderada")
        state = str(regional.get("regional_scope") or "BR")

        if demand >= 82:
            temp = "Muito aquecido"
            thesis = "alta procura e boa sustentação de preço"
        elif demand >= 68:
            temp = "Aquecido"
            thesis = "demanda favorável e negociação próxima da faixa indicada"
        elif demand >= 50:
            temp = "Estável"
            thesis = "oferta e procura em equilíbrio"
        elif demand >= 38:
            temp = "Saturado"
            thesis = "maior disputa entre anúncios semelhantes"
        else:
            temp = "Baixa demanda"
            thesis = "mercado mais lento e sensível a preço"

        bullets = [
            f"Temperatura {temp.lower()} na praça {state}, com {volume} comparáveis úteis.",
            "Preços pouco dispersos reforçam a faixa recomendada." if dispersion <= .14 else "A dispersão exige uma estratégia de anúncio mais cuidadosa.",
            f"Resistência de preço {resistance}; estratégia sugerida: {strategy.get('strategy_label', 'equilíbrio comercial')}.",
        ]
        if trend and trend != "estável":
            bullets.append(f"Tendência atual: {trend} no recorte analisado.")
        return {
            "market_temperature_label": temp,
            "market_temperature_score": demand,
            "market_thesis": thesis,
            "executive_market_insight_v2": f"O recorte indica mercado {temp.lower()}, {thesis}. A recomendação é anunciar dentro da faixa segura e ajustar conforme resposta dos primeiros contatos.",
            "market_insight_bullets": bullets,
        }
