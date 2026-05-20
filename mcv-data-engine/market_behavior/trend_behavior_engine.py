from __future__ import annotations
from typing import Any


class TrendBehaviorEngine:
    def analyze(self, snapshots: list[dict[str, Any]]) -> dict[str, Any]:
        ordered = sorted(snapshots, key=lambda s: str(s.get("mes") or s.get("data_snapshot") or ""))
        if len(ordered) < 2:
            return {
                "trend_direction": "Estável",
                "trend_strength": "Baixa amostra",
                "median_price_change": 0.0,
                "volume_change": 0.0,
                "trend_reason": "Histórico insuficiente para medir tendência; manter leitura conservadora.",
            }
        first, last = ordered[0], ordered[-1]
        first_price = float(first.get("preco_mediano") or 0)
        last_price = float(last.get("preco_mediano") or 0)
        first_vol = float(first.get("qtd_anuncios") or 0)
        last_vol = float(last.get("qtd_anuncios") or 0)
        price_change = round((last_price - first_price) / first_price, 4) if first_price else 0.0
        volume_change = round((last_vol - first_vol) / max(first_vol, 1), 4)
        direction = self._direction(price_change)
        return {
            "trend_direction": direction,
            "trend_strength": self._strength(abs(price_change), abs(volume_change)),
            "median_price_change": price_change,
            "volume_change": volume_change,
            "trend_reason": self._reason(direction, price_change, volume_change),
        }

    def _direction(self, price_change: float) -> str:
        if price_change >= 0.035:
            return "Em valorização"
        if price_change <= -0.035:
            return "Em queda"
        if abs(price_change) <= 0.015:
            return "Estável"
        return "Volátil"

    def _strength(self, price_change: float, volume_change: float) -> str:
        signal = max(price_change, volume_change / 2)
        if signal >= 0.08:
            return "Forte"
        if signal >= 0.035:
            return "Moderada"
        return "Leve"

    def _reason(self, direction: str, price_change: float, volume_change: float) -> str:
        pct = round(price_change * 100, 1)
        vol = round(volume_change * 100, 1)
        if direction == "Em valorização":
            return f"A mediana avançou {pct}% no histórico disponível, com variação de volume de {vol}%."
        if direction == "Em queda":
            return f"A mediana recuou {abs(pct)}% no histórico disponível, exigindo preço mais competitivo."
        if direction == "Volátil":
            return "A faixa mostra oscilação; recomenda-se usar percentis e comparáveis recentes."
        return "A mediana permanece estável no histórico disponível."
