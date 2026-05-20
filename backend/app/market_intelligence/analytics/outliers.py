from __future__ import annotations

import statistics


def quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0
    idx = (len(ordered) - 1) * q
    lo = int(idx)
    hi = min(lo + 1, len(ordered) - 1)
    w = idx - lo
    return ordered[lo] * (1 - w) + ordered[hi] * w


def remove_price_outliers(values: list[float]) -> list[float]:
    if len(values) < 5:
        return [v for v in values if v > 1000]
    q1, q3 = quantile(values, .25), quantile(values, .75)
    iqr = q3 - q1
    low, high = max(1000, q1 - 1.5 * iqr), q3 + 1.5 * iqr
    iqr_filtered = [v for v in values if low <= v <= high]
    if len(iqr_filtered) >= 5:
        mean = statistics.mean(iqr_filtered)
        stdev = statistics.pstdev(iqr_filtered) or 1
        return [v for v in iqr_filtered if abs((v - mean) / stdev) <= 2.8]
    return iqr_filtered


def is_suspicious_listing(row: dict) -> bool:
    price = float(row.get("price") or 0)
    year = int(row.get("year") or 0)
    mileage = int(row.get("mileage") or 0)
    return price < 5000 or price > 2000000 or year < 1970 or year > 2027 or mileage < 0 or mileage > 1000000
