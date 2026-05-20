from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from difflib import SequenceMatcher
from math import exp
from typing import Any
from sqlalchemy.orm import Session
from app.models.market import MarketListing
from app.market_intelligence.normalizers.vehicle_normalizer import normalize_brand, normalize_model, normalize_version, normalize_fuel, normalize_transmission, normalize_state

@dataclass
class ComparableMatch:
    listing: MarketListing
    similarity_score: int
    details: dict[str, Any]

class ComparableEngine:
    def __init__(self, min_score: int = 62):
        self.min_score = min_score

    def select(self, db: Session, vehicle: Any, limit: int = 40) -> list[ComparableMatch]:
        brand = normalize_brand(vehicle.brand)
        model = normalize_model(vehicle.model)
        candidates = db.query(MarketListing).filter(
            MarketListing.brand == brand,
            MarketListing.year.between(vehicle.year - 2, vehicle.year + 2),
        ).order_by(MarketListing.collected_at.desc()).limit(500).all()
        out: list[ComparableMatch] = []
        for row in candidates:
            score, details = self.score(vehicle, row)
            if score >= self.min_score:
                out.append(ComparableMatch(row, score, details))
        out.sort(key=lambda x: (x.similarity_score, x.listing.collected_at), reverse=True)
        return out[:limit]

    def score(self, vehicle: Any, item: MarketListing) -> tuple[int, dict[str, Any]]:
        vm, im = normalize_model(vehicle.model), normalize_model(item.model)
        vv, iv = normalize_version(getattr(vehicle, 'version', '')), normalize_version(item.version)
        model_ratio = SequenceMatcher(None, vm, im).ratio()
        version_ratio = SequenceMatcher(None, vv, iv).ratio() if vv and iv else .55
        year_delta = abs(vehicle.year - item.year)
        km_delta = abs(vehicle.km - item.mileage)
        state_equal = normalize_state(vehicle.state) == normalize_state(item.state)
        fuel_equal = normalize_fuel(getattr(vehicle, 'fuel', '')) and normalize_fuel(getattr(vehicle, 'fuel', '')) == normalize_fuel(item.fuel)
        trans_equal = normalize_transmission(getattr(vehicle, 'transmission', '')) and normalize_transmission(getattr(vehicle, 'transmission', '')) == normalize_transmission(item.transmission)
        recency = 8
        try:
            days = max(0, (datetime.now(timezone.utc) - item.collected_at).days)
            recency = int(10 * exp(-days / 90))
        except Exception:
            pass
        score = int(model_ratio * 30 + version_ratio * 12 + max(0, 18 - year_delta * 6) + max(0, 18 - min(18, km_delta / 6000)) + (12 if state_equal else 4) + (5 if fuel_equal else 1) + (5 if trans_equal else 1) + recency)
        return min(100, max(0, score)), {"model_ratio": round(model_ratio, 2), "version_ratio": round(version_ratio, 2), "year_delta": year_delta, "km_delta": km_delta, "same_state": state_equal, "same_fuel": bool(fuel_equal), "same_transmission": bool(trans_equal), "recency_score": recency}
