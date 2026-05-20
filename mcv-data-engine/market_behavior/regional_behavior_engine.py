from __future__ import annotations
from statistics import median
from typing import Any


class RegionalBehaviorEngine:
    def analyze(self, comparables: list[dict[str, Any]], state: str | None = None, city: str | None = None) -> dict[str, Any]:
        prices = [float(c["preco"]) for c in comparables if c.get("preco") is not None]
        if not prices:
            return {
                "regional_strength": "Baixa amostra",
                "regional_price_delta": 0.0,
                "regional_liquidity_level": "Indefinida",
                "regional_reason": "Sem comparáveis limpos suficientes para leitura regional.",
            }
        regional = [c for c in comparables if self._regional_match(c, state, city)]
        reg_prices = [float(c["preco"]) for c in regional if c.get("preco") is not None]
        national_med = float(median(prices))
        reg_med = float(median(reg_prices)) if reg_prices else national_med
        delta = round((reg_med - national_med) / national_med, 4) if national_med else 0.0
        liquidity = self._liquidity(len(regional), len(comparables))
        return {
            "regional_strength": self._strength(delta, len(regional)),
            "regional_price_delta": delta,
            "regional_liquidity_level": liquidity,
            "regional_reason": self._reason(delta, len(regional), state, city),
            "regional_sample_size": len(regional),
        }

    def _regional_match(self, row: dict[str, Any], state: str | None, city: str | None) -> bool:
        if city and row.get("cidade") and self._key(city) == self._key(row.get("cidade")):
            return True
        if state and row.get("estado") and str(state).upper() == str(row.get("estado")).upper():
            return True
        return False

    def _liquidity(self, regional_count: int, total_count: int) -> str:
        if regional_count >= 18:
            return "Alta"
        if regional_count >= 7:
            return "Média"
        if total_count >= 7:
            return "Baixa regional, usar referência ampliada"
        return "Baixa"

    def _strength(self, delta: float, regional_count: int) -> str:
        if regional_count < 4:
            return "Baixa amostra"
        if delta >= 0.04:
            return "Região valorizada"
        if delta <= -0.04:
            return "Região descontada"
        return "Região alinhada"

    def _reason(self, delta: float, count: int, state: str | None, city: str | None) -> str:
        location = city or state or "região informada"
        if count < 4:
            return f"Há poucos comparáveis diretos em {location}; a leitura usa amostra ampliada com cautela."
        if delta >= 0.04:
            return f"Em {location}, os comparáveis ficam acima da mediana geral da amostra."
        if delta <= -0.04:
            return f"Em {location}, os comparáveis ficam abaixo da mediana geral, indicando maior sensibilidade a preço."
        return f"Em {location}, os preços estão próximos da mediana geral dos comparáveis."

    def _key(self, value: Any) -> str:
        import re, unicodedata
        text = unicodedata.normalize("NFKD", str(value or "").lower())
        text = "".join(ch for ch in text if not unicodedata.combining(ch))
        return re.sub(r"[^a-z0-9]+", " ", text).strip()
