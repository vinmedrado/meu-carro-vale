from __future__ import annotations
from statistics import median
from typing import Any


class ResistanceEngine:
    def analyze(self, comparables: list[dict[str, Any]], target_price: float | None = None, pressure_score: float = 0.0, velocity_score: float = 0.0) -> dict[str, Any]:
        prices = sorted(float(c["preco"]) for c in comparables if c.get("preco") is not None)
        if not prices:
            return {
                "resistance_price": None,
                "resistance_level": "Indefinida",
                "stuck_risk": "Moderado",
                "stuck_risk_score": 0.5,
                "resistance_reason": "Amostra insuficiente para definir teto de resistência com segurança.",
            }
        med = float(median(prices))
        p75 = self._quantile(prices, 0.75)
        p90 = self._quantile(prices, 0.90)
        resistance_price = round(max(p75, med * 1.06), 2)
        if len(prices) >= 8:
            resistance_price = round(min(resistance_price, p90), 2)
        above = 0.0 if not target_price else max(0.0, (float(target_price) - resistance_price) / max(resistance_price, 1))
        score = round(min(1.0, pressure_score * 0.45 + (1 - velocity_score) * 0.35 + above * 1.6), 3)
        return {
            "resistance_price": resistance_price,
            "resistance_level": self._level(score),
            "stuck_risk": self._risk(score),
            "stuck_risk_score": score,
            "resistance_reason": self._reason(score, resistance_price),
            "p75": round(p75, 2),
            "p90": round(p90, 2),
        }

    def _level(self, score: float) -> str:
        if score >= 0.70:
            return "Alta resistência"
        if score >= 0.45:
            return "Resistência moderada"
        return "Baixa resistência"

    def _risk(self, score: float) -> str:
        if score >= 0.70:
            return "Alto"
        if score >= 0.40:
            return "Moderado"
        return "Baixo"

    def _reason(self, score: float, resistance_price: float) -> str:
        if score >= 0.70:
            return f"Acima de R$ {resistance_price:,.0f}, comparáveis indicam maior risco de baixa liquidez.".replace(",", ".")
        if score >= 0.40:
            return f"A partir de R$ {resistance_price:,.0f}, o preço deve ser defendido com bons argumentos de estado, km e região.".replace(",", ".")
        return "A faixa atual apresenta baixa resistência relativa frente aos comparáveis limpos."

    def _quantile(self, values: list[float], q: float) -> float:
        pos = (len(values) - 1) * q
        lower = int(pos)
        upper = min(lower + 1, len(values) - 1)
        weight = pos - lower
        return values[lower] * (1 - weight) + values[upper] * weight
