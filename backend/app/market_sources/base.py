from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol


@dataclass
class MarketSearchQuery:
    brand: str
    model: str
    year: int | None = None
    state: str | None = None


@dataclass
class MarketSourceListing:
    title: str
    price: float
    brand: str
    model: str
    version: str = ""
    year: int = 0
    mileage: int = 0
    city: str = ""
    state: str = ""
    transmission: str = ""
    fuel: str = ""
    link: str = ""
    source: str = ""
    collected_at: str = datetime.now(timezone.utc).isoformat()


class MarketSourceAdapter(Protocol):
    source_name: str
    enabled: bool

    def search(self, query: MarketSearchQuery) -> list[MarketSourceListing]: ...


class DisabledMarketplaceAdapter:
    source_name = "disabled"
    enabled = False
    reason = "Adaptador preparado, mas desabilitado para respeitar robots.txt, termos da plataforma ou ausência de API/parceria."

    def search(self, query: MarketSearchQuery) -> list[MarketSourceListing]:
        return []
