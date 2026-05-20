from __future__ import annotations

from statistics import median
from typing import Any


class PricePressureEngine:
    """Calcula pressão de preço usando comparáveis limpos, não anúncios brutos."""

    def analyze(self, comparables: list[dict[str, Any]], target_price: float | None = None) -> dict[str, Any]:
        prices = sorted(float(c["preco"]) for c in comparables if c.get("preco") is not None)
        if not prices:
            return {
                "price_pressure_score": 0.0,
                "pressure_level": "Baixa amostra",
                "pressure_reason": "Não há comparáveis limpos suficientes para medir pressão de preço.",
            }
        med = float(median(prices))
        p25 = self._quantile(prices, 0.25)
        p75 = self._quantile(prices, 0.75)
        dispersion = (p75 - p25) / med if med else 0.0
        below_med = len([p for p in prices if p < med]) / len(prices)
        above_reference = 0.0
        if target_price:
            above_reference = max(0.0, (float(target_price) - med) / med)
        supply_factor = min(len(prices) / 60, 1.0)
        score = round(min(1.0, dispersion * 1.35 + supply_factor * 0.30 + below_med * 0.20 + above_reference * 1.10), 3)
        level = self._level(score)
        reason = self._reason(level, len(prices), dispersion, med, target_price)
        return {
            "price_pressure_score": score,
            "pressure_level": level,
            "pressure_reason": reason,
            "median_price": round(med, 2),
            "p25": round(p25, 2),
            "p75": round(p75, 2),
            "price_dispersion": round(dispersion, 4),
            "sample_size": len(prices),
        }

    def _level(self, score: float) -> str:
        if score >= 0.72:
            return "Mercado pressionado"
        if score >= 0.52:
            return "Pressão alta"
        if score >= 0.32:
            return "Pressão moderada"
        return "Pressão baixa"

    def _reason(self, level: str, volume: int, dispersion: float, median_price: float, target_price: float | None) -> str:
        if level == "Pressão baixa":
            return "A amostra apresenta preços próximos entre si, indicando menor pressão para descontos agressivos."
        if target_price and target_price > median_price * 1.08:
            return "O preço informado está acima da mediana dos comparáveis, aumentando a resistência do mercado."
        if dispersion > 0.22:
            return "A dispersão de preços é elevada, o que costuma aumentar negociação e comparação por parte dos compradores."
        if volume >= 40:
            return "Há oferta relevante de anúncios semelhantes, criando maior disputa por atenção do comprador."
        return "Existe pressão moderada por preço, mas a faixa ainda permite negociação com segurança."

    def _quantile(self, values: list[float], q: float) -> float:
        if not values:
            return 0.0
        pos = (len(values) - 1) * q
        lower = int(pos)
        upper = min(lower + 1, len(values) - 1)
        weight = pos - lower
        return values[lower] * (1 - weight) + values[upper] * weight
