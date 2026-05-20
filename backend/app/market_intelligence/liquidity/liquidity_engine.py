from __future__ import annotations

import statistics
from dataclasses import dataclass

@dataclass
class LiquidityResult:
    score: int
    label: str
    listing_count: int
    dispersion: float
    regional_volume: int

class LiquidityEngine:
    def calculate(self, prices: list[float], regional_count: int = 0, update_velocity: float = 0.0) -> LiquidityResult:
        count = len(prices)
        if count >= 2:
            median = statistics.median(prices) or 1
            dispersion = (statistics.pstdev(prices) / median)
        else:
            dispersion = .65
        score = 35 + min(35, count * 3) + min(15, regional_count * 2) + min(10, update_velocity * 2) - min(25, dispersion * 45)
        score = int(max(15, min(100, score)))
        label = "Muito Alta" if score >= 82 else "Alta" if score >= 68 else "Média" if score >= 48 else "Baixa"
        return LiquidityResult(score, label, count, round(dispersion, 3), regional_count)
