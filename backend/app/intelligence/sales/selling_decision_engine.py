from __future__ import annotations

from typing import Any

from .utils import clamp, money


class SellingDecisionEngine:
    """Camada consultiva de venda em português.

    Deriva preço de anúncio, faixa de fechamento, semáforo de proposta,
    defesa comercial e risco de ficar parado usando somente valuation,
    liquidez, comparáveis, dispersão e confiança já calculados.
    """

    def analyze(
        self,
        valuation: dict[str, Any],
        negotiation: dict[str, Any],
        liquidity: dict[str, Any],
        confidence: dict[str, Any],
        comparables: dict[str, Any],
        positioning: dict[str, Any] | None = None,
        buyer_behavior: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        positioning = positioning or {}
        buyer_behavior = buyer_behavior or {}
        ideal = float(
            negotiation.get("recommended_price")
            or valuation.get("ideal_price")
            or valuation.get("market_reference")
            or 0
        )
        quick = float(negotiation.get("quick_sale_price") or valuation.get("quick_sale_price") or ideal * 0.94)
        floor = float(negotiation.get("negotiation_floor") or quick or ideal * 0.94)
        ceiling = float(negotiation.get("negotiation_ceiling") or valuation.get("recommended_top_price") or ideal * 1.06)
        demand = int(liquidity.get("demand_index") or 50)
        confidence_score = int(confidence.get("confidence_score") or valuation.get("confidence_score") or 60)
        dispersion = float(comparables.get("price_dispersion_index") or 0)
        comparables_used = int(comparables.get("comparables_used") or valuation.get("comparables_used") or 0)
        percentile = int(positioning.get("market_position_percentile") or valuation.get("market_position_percentile") or 50)
        pressure = int(liquidity.get("pressure_score") or valuation.get("pressure_score") or 50)

        listing_multiplier = 1.018 if demand >= 70 and confidence_score >= 68 else 1.01 if demand >= 52 else 0.997
        listing_price = self._psychological_price(money(clamp(ideal * listing_multiplier, floor, max(ceiling, ideal))))
        ideal_min = money(max(floor, ideal * (0.962 if demand >= 62 else 0.942)))
        ideal_max = money(min(max(ceiling, ideal_min), ideal * (1.045 if confidence_score >= 70 else 1.028)))
        minimum = money(max(quick, ideal_min * (0.982 if demand >= 60 else 0.965)))
        resistance_price = max(money(ceiling), self._psychological_price(money(max(ceiling, listing_price * (1.018 if demand >= 72 else 1.008)))))
        stuck_risk = self._stuck_risk(demand, confidence_score, dispersion, percentile, pressure, comparables_used)
        days = 10 if stuck_risk[0] == "Alto" else 14 if stuck_risk[0] == "Moderado" else 18
        cut = 3 if stuck_risk[0] == "Alto" else 2 if stuck_risk[0] == "Moderado" else 1

        signal = self.classify_offer(ideal_min, ideal_max, minimum, proposed_price=None)
        defense = self._defense_arguments(demand, confidence_score, dispersion, comparables_used, buyer_behavior, positioning)
        summary = self._seller_summary(listing_price, ideal_min, ideal_max, minimum, stuck_risk[0], defense)

        return {
            "listing_price": listing_price,
            "ideal_close_range_min": ideal_min,
            "ideal_close_range_max": ideal_max,
            "minimum_recommended_price": minimum,
            "resistance_price": resistance_price,
            "stuck_risk_level": stuck_risk[0],
            "stuck_risk_reason": stuck_risk[1],
            "review_price_after_days": days,
            "suggested_price_cut_percent": cut,
            "negotiation_signal": signal["signal"],
            "negotiation_message": signal["message"],
            "price_defense_arguments": defense,
            "seller_summary": summary,
            "psychological_price_note": f"{self._format_money(listing_price)} tem leitura comercial melhor para anúncio do que um número redondo próximo.",
            "proposal_reference": {
                "green_from": ideal_min,
                "yellow_from": minimum,
                "red_below": minimum,
            },
        }

    def classify_offer(self, ideal_min: float, ideal_max: float, minimum: float, proposed_price: float | None) -> dict[str, str]:
        if proposed_price is None:
            return {"signal": "Aguardando proposta", "message": "Digite uma proposta recebida para comparar com a faixa recomendada."}
        if proposed_price >= ideal_min:
            return {"signal": "Boa proposta", "message": "A proposta está dentro ou acima da faixa ideal de fechamento."}
        if proposed_price >= minimum:
            return {"signal": "Negociar com cuidado", "message": "A proposta ainda pode fazer sentido, mas tente aproximar da faixa ideal antes de aceitar."}
        return {"signal": "Proposta abaixo do recomendado", "message": "Você pode estar deixando dinheiro na mesa. Use os comparáveis e a liquidez para defender o valor."}

    def _psychological_price(self, value: float) -> int:
        rounded = int(round(value / 100) * 100)
        if rounded <= 1000:
            return rounded
        return max(0, rounded - 100)

    def _stuck_risk(self, demand: int, confidence: int, dispersion: float, percentile: int, pressure: int, sample: int) -> tuple[str, str]:
        risk_points = 0
        risk_points += max(0, 62 - demand) * 0.85
        risk_points += max(0, percentile - 62) * 0.55
        risk_points += max(0, pressure - 55) * 0.65
        risk_points += min(28, dispersion * 110)
        risk_points += 10 if sample < 5 else 4 if sample < 9 else 0
        risk_points -= 8 if confidence >= 75 else 0
        if risk_points >= 46:
            return "Alto", "Acima da faixa recomendada, anúncios semelhantes tendem a perder competitividade e gerar menos contatos."
        if risk_points >= 25:
            return "Moderado", "Há espaço para defender preço, mas a resposta dos contatos deve ser acompanhada nos primeiros dias."
        return "Baixo", "A faixa está competitiva para o recorte analisado, com menor chance de o anúncio ficar parado."

    def _defense_arguments(self, demand: int, confidence: int, dispersion: float, sample: int, buyer_behavior: dict[str, Any], positioning: dict[str, Any]) -> list[str]:
        args: list[str] = []
        if sample >= 8:
            args.append("Valor alinhado com uma amostra consistente de comparáveis semelhantes.")
        else:
            args.append("Faixa calculada de forma conservadora por haver poucos comparáveis diretos.")
        if demand >= 68:
            args.append("Modelo com boa liquidez regional, o que fortalece a defesa do preço.")
        else:
            args.append("Preço posicionado para equilibrar margem e velocidade de venda.")
        if dispersion <= 0.16:
            args.append("Baixa dispersão indica mercado mais estável para esse perfil de veículo.")
        else:
            args.append("Dispersão dos anúncios exige negociar com base em estado, histórico e quilometragem.")
        if str(buyer_behavior.get("km_sensitivity") or "").lower() in {"alta", "média"}:
            args.append("Compradores tendem a valorizar quilometragem bem justificada nesse segmento.")
        if positioning.get("market_position_percentile"):
            args.append(f"Posicionamento comparado a anúncios semelhantes: acima de {int(positioning.get('market_position_percentile') or 0)}% da amostra.")
        return args[:5]

    def _seller_summary(self, listing: int, close_min: int, close_max: int, minimum: int, risk: str, defense: list[str]) -> str:
        return (
            f"Anuncie em {self._format_money(listing)}, negocie dentro da faixa de "
            f"{self._format_money(close_min)} a {self._format_money(close_max)} e evite aceitar abaixo de "
            f"{self._format_money(minimum)}. Risco de ficar parado: {risk.lower()}. "
            f"Principal argumento: {defense[0] if defense else 'valor alinhado aos comparáveis analisados.'}"
        )

    def _format_money(self, value: float) -> str:
        return f"R$ {int(value):,}".replace(",", ".")
