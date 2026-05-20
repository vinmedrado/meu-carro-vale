from __future__ import annotations

import hashlib
import re
from typing import Any

from app.intelligence.schemas.core import NormalizedMarketListing, NormalizedVehicleQuery

UF_RE = re.compile(r"^[A-Z]{2}$")
SPACE_RE = re.compile(r"\s+")


def normalize_text(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9áéíóúâêôãõç/ .-]", " ", text)
    return SPACE_RE.sub(" ", text).strip()


def normalize_state(value: Any) -> str:
    state = str(value or "").strip().upper()[:2]
    return state if UF_RE.match(state) else ""


def normalize_vehicle_query(vehicle: Any) -> NormalizedVehicleQuery:
    return NormalizedVehicleQuery(
        brand=normalize_text(getattr(vehicle, "brand", "")),
        model=normalize_text(getattr(vehicle, "model", "")),
        version=normalize_text(getattr(vehicle, "version", "")),
        year=int(getattr(vehicle, "year", 0) or 0),
        mileage=int(getattr(vehicle, "km", getattr(vehicle, "mileage", 0)) or 0),
        state=normalize_state(getattr(vehicle, "state", "")),
        city=normalize_text(getattr(vehicle, "city", "")),
        fuel=normalize_text(getattr(vehicle, "fuel", "")),
        transmission=normalize_text(getattr(vehicle, "transmission", "")),
    )


def listing_fingerprint(item: NormalizedMarketListing) -> str:
    base = "|".join([
        item.source,
        item.brand,
        item.model,
        item.version,
        str(item.year),
        str(round(item.price / 100) * 100),
        item.state,
        item.city,
        str(round(item.mileage / 1000) * 1000),
    ])
    return hashlib.sha1(base.encode("utf-8")).hexdigest()


def normalize_listing(raw: dict[str, Any], source: str) -> NormalizedMarketListing:
    return NormalizedMarketListing(
        source=source,
        external_id=str(raw.get("external_id") or raw.get("id") or ""),
        title=str(raw.get("title") or "").strip(),
        brand=normalize_text(raw.get("brand")),
        model=normalize_text(raw.get("model")),
        version=normalize_text(raw.get("version")),
        year=int(raw.get("year") or 0),
        mileage=int(raw.get("mileage") or raw.get("km") or 0),
        price=float(raw.get("price") or 0),
        state=normalize_state(raw.get("state")),
        city=normalize_text(raw.get("city")),
        fuel=normalize_text(raw.get("fuel")),
        transmission=normalize_text(raw.get("transmission")),
        url=str(raw.get("url") or ""),
        seller_type=normalize_text(raw.get("seller_type")),
        raw=raw,
    )
