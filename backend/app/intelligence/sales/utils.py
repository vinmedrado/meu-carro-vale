from __future__ import annotations

from typing import Any


def money(value: float | int | None) -> int:
    return int(round(float(value or 0) / 100) * 100)


def pct(value: float | int | None, digits: int = 1) -> float:
    return round(float(value or 0), digits)


def prices_from(comparables: dict[str, Any]) -> list[float]:
    return [float(item.get("price") or 0) for item in comparables.get("comparables", []) if float(item.get("price") or 0) > 0]


def percentile_rank(value: float, values: list[float]) -> int:
    if not values or not value:
        return 50
    below = len([x for x in values if x <= value])
    return int(max(1, min(99, round((below / len(values)) * 100))))


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))
