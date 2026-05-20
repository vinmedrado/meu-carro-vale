from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class NormalizedVehicleQuery:
    brand: str
    model: str
    version: str
    year: int
    mileage: int
    state: str
    city: str = ""
    fuel: str = ""
    transmission: str = ""
    engine: str = ""


@dataclass(frozen=True)
class NormalizedMarketListing:
    source: str
    external_id: str
    title: str
    brand: str
    model: str
    version: str
    year: int
    mileage: int
    price: float
    state: str
    city: str = ""
    fuel: str = ""
    transmission: str = ""
    url: str = ""
    seller_type: str = ""
    collected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ComparableCandidate:
    listing_id: int | None
    title: str
    price: float
    source: str
    year: int
    mileage: int
    city: str
    state: str
    similarity_score: int
    regional_similarity: int
    km_similarity: int
    market_distance: float
    details: dict[str, Any] = field(default_factory=dict)
