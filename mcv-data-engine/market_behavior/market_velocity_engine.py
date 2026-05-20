from __future__ import annotations

from datetime import date, datetime
from typing import Any


class MarketVelocityEngine:
    def analyze(self, comparables: list[dict[str, Any]], snapshots: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        count = len(comparables)
        recent_ratio = self._recent_ratio(comparables)
        snapshot_stability = self._snapshot_stability(snapshots or [])
        score = round(min(1.0, (min(count / 35, 1.0) * 0.45) + (recent_ratio * 0.35) + (snapshot_stability * 0.20)), 3)
        level = self._level(score)
        return {
            "market_velocity_score": score,
            "velocity_level": level,
            "estimated_sale_window": self._sale_window(score, count),
            "velocity_reason": self._reason(level, count, recent_ratio),
            "recent_listing_ratio": round(recent_ratio, 3),
        }

    def _recent_ratio(self, rows: list[dict[str, Any]]) -> float:
        if not rows:
            return 0.0
        recent = 0
        for row in rows:
            dt = self._parse_date(row.get("data_coleta") or row.get("data_publicacao"))
            if dt and (date.today() - dt).days <= 30:
                recent += 1
        return recent / len(rows)

    def _snapshot_stability(self, snapshots: list[dict[str, Any]]) -> float:
        if not snapshots:
            return 0.55
        dispersions = [float(s.get("dispersao_preco") or 0.0) for s in snapshots]
        avg_dispersion = sum(dispersions) / max(len(dispersions), 1)
        return max(0.0, min(1.0, 1 - avg_dispersion / 0.35))

    def _level(self, score: float) -> str:
        if score >= 0.75:
            return "Muito rápida"
        if score >= 0.58:
            return "Boa velocidade"
        if score >= 0.38:
            return "Velocidade moderada"
        return "Baixa velocidade"

    def _sale_window(self, score: float, count: int) -> str:
        if score >= 0.75:
            return "10 a 18 dias"
        if score >= 0.58:
            return "18 a 30 dias"
        if count >= 6:
            return "30 a 45 dias"
        return "acima de 45 dias"

    def _reason(self, level: str, count: int, recent_ratio: float) -> str:
        if level in {"Muito rápida", "Boa velocidade"}:
            return "Mercado com boa velocidade: há volume e recência suficientes entre comparáveis limpos."
        if count < 6:
            return "A amostra regional é pequena, reduzindo previsibilidade de giro."
        if recent_ratio < 0.35:
            return "Poucos comparáveis recentes indicam menor velocidade de renovação dos anúncios."
        return "A velocidade é moderada e depende de preço competitivo dentro da faixa dos comparáveis."

    def _parse_date(self, value: Any) -> date | None:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value).replace("Z", "").split("+")[0]).date()
        except Exception:
            return None
