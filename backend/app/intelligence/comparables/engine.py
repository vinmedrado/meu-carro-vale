from __future__ import annotations

import statistics
from difflib import SequenceMatcher
from typing import Any

from sqlalchemy.orm import Session

from app.intelligence.normalization.vehicle import normalize_vehicle_query
from app.intelligence.schemas.core import ComparableCandidate
from app.models.market import MarketListing


def _ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.45
    return SequenceMatcher(None, a, b).ratio()


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = (len(ordered) - 1) * q
    lo = int(idx)
    hi = min(lo + 1, len(ordered) - 1)
    w = idx - lo
    return ordered[lo] * (1 - w) + ordered[hi] * w


class ComparableEngine:
    """Seleciona comparáveis com ranking, remoção de outliers e métricas explicáveis."""

    def __init__(self, min_similarity: int = 58, max_candidates: int = 500) -> None:
        self.min_similarity = min_similarity
        self.max_candidates = max_candidates

    def analyze(self, db: Session, vehicle: Any, limit: int = 18) -> dict[str, Any]:
        query = normalize_vehicle_query(vehicle)
        rows = (
            db.query(MarketListing)
            .filter(MarketListing.brand == query.brand, MarketListing.year.between(query.year - 2, query.year + 2))
            .order_by(MarketListing.collected_at.desc())
            .limit(self.max_candidates)
            .all()
        )
        ranked = [self._score(query, row) for row in rows]
        ranked = [item for item in ranked if item.similarity_score >= self.min_similarity and item.price > 5000]
        ranked.sort(key=lambda x: (x.similarity_score, -x.market_distance), reverse=True)
        filtered, outliers_removed = self._remove_outliers(ranked)
        selected = filtered[:limit]
        prices = [item.price for item in selected]
        dispersion = 0.0
        if len(prices) >= 2 and statistics.median(prices):
            dispersion = round(statistics.pstdev(prices) / statistics.median(prices), 4)
        return {
            "comparables_used": len(selected),
            "similarity_score": round(statistics.mean([x.similarity_score for x in selected]), 1) if selected else 0,
            "regional_similarity": round(statistics.mean([x.regional_similarity for x in selected]), 1) if selected else 0,
            "km_similarity": round(statistics.mean([x.km_similarity for x in selected]), 1) if selected else 0,
            "market_distance": round(statistics.mean([x.market_distance for x in selected]), 3) if selected else 0,
            "outliers_removed": outliers_removed,
            "price_dispersion_index": dispersion,
            "percentiles": {
                "p10": round(_percentile(prices, .10), 2),
                "p25": round(_percentile(prices, .25), 2),
                "p50": round(_percentile(prices, .50), 2),
                "p75": round(_percentile(prices, .75), 2),
                "p90": round(_percentile(prices, .90), 2),
            },
            "comparables": [candidate.__dict__ for candidate in selected],
        }

    def _score(self, query: Any, row: MarketListing) -> ComparableCandidate:
        model_ratio = _ratio(query.model, str(row.model or "").lower())
        version_ratio = _ratio(query.version, str(row.version or "").lower()) if query.version else 0.55
        year_distance = abs(query.year - int(row.year or query.year))
        km_distance = abs(query.mileage - int(row.mileage or query.mileage))
        km_similarity = int(max(0, 100 - min(100, km_distance / 700)))
        regional_similarity = 100 if query.state and query.state == (row.state or "").upper() else 72 if row.state else 50
        fuel_bonus = 4 if query.fuel and query.fuel in str(row.fuel or "").lower() else 0
        trans_bonus = 4 if query.transmission and query.transmission in str(row.transmission or "").lower() else 0
        score = int(model_ratio * 30 + version_ratio * 12 + max(0, 18 - year_distance * 6) + km_similarity * .18 + regional_similarity * .14 + fuel_bonus + trans_bonus)
        market_distance = round((year_distance * 0.18) + (km_distance / 100000) + (0 if regional_similarity == 100 else .14), 3)
        return ComparableCandidate(
            listing_id=row.id,
            title=row.title,
            price=float(row.price or 0),
            source=row.source,
            year=row.year,
            mileage=row.mileage,
            city=row.city,
            state=row.state,
            similarity_score=max(0, min(100, score)),
            regional_similarity=regional_similarity,
            km_similarity=km_similarity,
            market_distance=market_distance,
            details={"model_ratio": round(model_ratio, 2), "version_ratio": round(version_ratio, 2), "year_distance": year_distance, "km_distance": km_distance},
        )

    def _remove_outliers(self, items: list[ComparableCandidate]) -> tuple[list[ComparableCandidate], int]:
        if len(items) < 6:
            return items, 0
        prices = [item.price for item in items]
        q1 = _percentile(prices, .25)
        q3 = _percentile(prices, .75)
        iqr = q3 - q1
        low = q1 - 1.5 * iqr
        high = q3 + 1.5 * iqr
        filtered = [item for item in items if low <= item.price <= high]
        return filtered, len(items) - len(filtered)
