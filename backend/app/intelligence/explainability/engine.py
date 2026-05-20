from __future__ import annotations

from typing import Any


def _money(value: float) -> int:
    return int(round(value / 100) * 100)


class ExplainableValuationEngine:
    """Gera explicabilidade consultiva a partir dos fatores calculados.

    Não inventa dados: usa comparáveis, liquidez, confiança, regionalização e
    tendências já produzidos pela MCV Intelligence Engine. Quando a base é
    pequena, a explicação assume caráter exploratório e informa essa limitação.
    """

    def analyze(
        self,
        vehicle: Any,
        valuation: dict[str, Any],
        comparables: dict[str, Any],
        liquidity: dict[str, Any],
        confidence: dict[str, Any],
        regional: dict[str, Any],
        trends: dict[str, Any],
        negotiation: dict[str, Any],
    ) -> dict[str, Any]:
        base = float(valuation.get("ideal_price") or valuation.get("market_reference") or negotiation.get("recommended_price") or 0)
        if base <= 0:
            base = float(valuation.get("fipe_real") or valuation.get("fipe_simulated") or 0)
        factors = self._factor_impacts(vehicle, base, comparables, liquidity, confidence, regional, trends)
        comparable_analysis = self._comparable_analysis(base, comparables.get("comparables") or [])
        positive = sum(item["impact_value"] for item in factors if item["impact_value"] > 0)
        negative = sum(item["impact_value"] for item in factors if item["impact_value"] < 0)
        insight = self._executive_insight(comparables, liquidity, confidence, regional, trends, negotiation)
        return {
            "valuation_explanation": factors,
            "valuation_explanation_text": self._human_summary(factors, comparables, confidence),
            "positive_impact_total": _money(positive),
            "negative_impact_total": _money(negative),
            "comparable_analysis": comparable_analysis,
            "executive_market_insight": insight,
            "market_temperature_detail": self._temperature_detail(liquidity),
            "regional_explanation": self._regional_explanation(regional, comparables),
            "negotiation_intelligence": self._negotiation_copy(negotiation, liquidity),
        }

    def _factor_impacts(self, vehicle: Any, base: float, comparables: dict[str, Any], liquidity: dict[str, Any], confidence: dict[str, Any], regional: dict[str, Any], trends: dict[str, Any]) -> list[dict[str, Any]]:
        count = int(comparables.get("comparables_used") or 0)
        avg_km = self._avg([float(item.get("mileage") or 0) for item in comparables.get("comparables", []) if item.get("mileage")])
        vehicle_km = float(getattr(vehicle, "km", getattr(vehicle, "mileage", 0)) or 0)
        demand = int(liquidity.get("demand_index") or 50)
        dispersion = float(comparables.get("price_dispersion_index") or 0)
        regional_delta = float(regional.get("regional_price_delta") or 0)
        similarity = float(comparables.get("similarity_score") or 0)
        impacts: list[dict[str, Any]] = []
        if avg_km and vehicle_km:
            km_delta_pct = (avg_km - vehicle_km) / max(avg_km, 1)
            impact = max(-0.035, min(0.045, km_delta_pct * 0.11)) * base
            impacts.append(self._item("Quilometragem", impact, 24, "km abaixo da média dos comparáveis" if impact > 0 else "km acima da média dos comparáveis"))
        if demand >= 65:
            impacts.append(self._item("Demanda regional", base * min(0.035, (demand - 60) / 1000), 22, "procura acima da média para o perfil analisado"))
        elif demand < 48:
            impacts.append(self._item("Demanda regional", -base * min(0.03, (50 - demand) / 900), 22, "procura mais lenta para o perfil analisado"))
        if dispersion:
            impact = -base * min(0.028, dispersion * 0.08) if dispersion >= .18 else base * min(0.018, (0.18 - dispersion) * 0.06)
            impacts.append(self._item("Dispersão de preços", impact, 18, "preços consistentes entre comparáveis" if impact > 0 else "amostra com preços mais espalhados"))
        if regional_delta:
            impacts.append(self._item("Comportamento regional", base * (regional_delta / 100), 16, "praça acima da média nacional" if regional_delta > 0 else "praça abaixo da média nacional"))
        if similarity >= 76:
            impacts.append(self._item("Aderência dos comparáveis", base * .014, 12, "comparáveis próximos em versão, ano, km e região"))
        elif count and similarity < 62:
            impacts.append(self._item("Aderência dos comparáveis", -base * .018, 12, "comparáveis úteis, porém menos próximos do veículo"))
        trend = str(trends.get("trend_direction") or "estável")
        if trend == "alta":
            impacts.append(self._item("Tendência de mercado", base * .012, 8, "mercado com sinal de valorização no recorte atual"))
        elif trend == "queda":
            impacts.append(self._item("Tendência de mercado", -base * .014, 8, "mercado com sinal de enfraquecimento no recorte atual"))
        if not impacts:
            impacts.append(self._item("Qualidade da amostra", 0, 100, str(confidence.get("confidence_reason") or "base ainda insuficiente para decomposição detalhada")))
        return impacts

    def _comparable_analysis(self, base: float, comparables: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows = []
        for item in comparables[:10]:
            price = float(item.get("price") or 0)
            diff = price - base if base else 0
            rows.append({
                "listing_id": item.get("listing_id"),
                "title": item.get("title"),
                "source": item.get("source"),
                "price": _money(price),
                "similarity_score": int(item.get("similarity_score") or 0),
                "km_difference": int(item.get("details", {}).get("km_distance") or 0),
                "regional_similarity": int(item.get("regional_similarity") or 0),
                "market_distance": float(item.get("market_distance") or 0),
                "valuation_impact": _money(diff),
                "reading": "acima da faixa central" if diff > base * .025 else "abaixo da faixa central" if diff < -base * .025 else "alinhado à faixa central",
            })
        return rows

    def _executive_insight(self, comparables: dict[str, Any], liquidity: dict[str, Any], confidence: dict[str, Any], regional: dict[str, Any], trends: dict[str, Any], negotiation: dict[str, Any]) -> str:
        confidence_level = str(confidence.get("confidence_level") or "em análise").lower()
        liquidity_level = str(liquidity.get("liquidity_level") or "em análise").lower()
        dispersion = float(comparables.get("price_dispersion_index") or 0)
        dispersion_text = "baixa dispersão de preços" if dispersion and dispersion <= .14 else "dispersão controlada" if dispersion <= .24 else "dispersão relevante entre anúncios"
        position = str(negotiation.get("positioning") or "equilibrado")
        regional_scope = regional.get("regional_scope") or "BR"
        return f"O veículo apresenta liquidez {liquidity_level}, confiança {confidence_level} e {dispersion_text} na praça {regional_scope}. A estratégia sugerida é posicionamento {position}, com negociação próxima da faixa recomendada quando a urgência de venda for baixa."

    def _human_summary(self, factors: list[dict[str, Any]], comparables: dict[str, Any], confidence: dict[str, Any]) -> str:
        main = sorted(factors, key=lambda x: abs(float(x.get("impact_value") or 0)), reverse=True)[:3]
        pieces = []
        for item in main:
            signal = "+" if item["impact_value"] > 0 else "-" if item["impact_value"] < 0 else ""
            pieces.append(f"{signal}R$ {abs(item['impact_value']):,.0f}".replace(",", ".") + f" por {item['reason']}")
        count = int(comparables.get("comparables_used") or 0)
        return f"A análise considera {count} comparáveis e qualidade {confidence.get('analysis_quality', 'em análise')}. " + "; ".join(pieces) + "."

    def _temperature_detail(self, liquidity: dict[str, Any]) -> str:
        temperature = str(liquidity.get("market_temperature") or "Estável")
        demand = int(liquidity.get("demand_index") or 50)
        if demand >= 82:
            level = "Muito aquecido"
            reason = "alta procura e boa velocidade estimada de venda"
        elif demand >= 68:
            level = "Aquecido"
            reason = "demanda favorável para o perfil do veículo"
        elif demand >= 50:
            level = "Estável"
            reason = "oferta e procura em equilíbrio"
        elif demand >= 38:
            level = "Saturado"
            reason = "negociação pode exigir preço mais competitivo"
        else:
            level = "Baixa demanda"
            reason = "mercado mais lento para este recorte"
        return f"{level}: {reason}. Leitura base: {temperature}."

    def _regional_explanation(self, regional: dict[str, Any], comparables: dict[str, Any]) -> str:
        delta = float(regional.get("regional_price_delta") or 0)
        scope = regional.get("regional_scope") or "BR"
        confidence = regional.get("regional_confidence") or "em análise"
        if delta > 0:
            return f"Na região {scope}, o recorte indica valorização de {delta:.2f}% sobre a referência nacional, com confiança regional {confidence}."
        if delta < 0:
            return f"Na região {scope}, o recorte indica ajuste de {abs(delta):.2f}% abaixo da referência nacional, com confiança regional {confidence}."
        return f"Na região {scope}, a leitura está próxima da média nacional; {comparables.get('regional_similarity', 0)} pontos de aderência regional."

    def _negotiation_copy(self, negotiation: dict[str, Any], liquidity: dict[str, Any]) -> dict[str, Any]:
        days = int(liquidity.get("average_days_on_market_estimate") or 0)
        return {
            "quick_sale_price": negotiation.get("quick_sale_price"),
            "ideal_listing_range": [negotiation.get("recommended_price"), negotiation.get("negotiation_ceiling")],
            "negotiation_floor": negotiation.get("negotiation_floor"),
            "negotiation_ceiling": negotiation.get("negotiation_ceiling"),
            "estimated_negotiation_margin": negotiation.get("estimated_negotiation_margin"),
            "estimated_sale_time": f"{max(7, days - 4)} a {days + 4} dias" if days else "estimativa dependente de novos comparáveis",
        }

    def _item(self, factor: str, impact: float, weight: int, reason: str) -> dict[str, Any]:
        return {"factor": factor, "impact_value": _money(impact), "impact_direction": "positivo" if impact > 0 else "negativo" if impact < 0 else "neutro", "weight": weight, "reason": reason}

    def _avg(self, values: list[float]) -> float:
        return sum(values) / len(values) if values else 0.0
