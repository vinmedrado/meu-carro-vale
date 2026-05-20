from __future__ import annotations

from app.intelligence.providers.base import MarketProvider


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, MarketProvider] = {}

    def register(self, provider: MarketProvider) -> None:
        self._providers[provider.source_name] = provider

    def enabled_sources(self) -> list[str]:
        return sorted(self._providers)

    def all(self) -> list[MarketProvider]:
        return list(self._providers.values())


registry = ProviderRegistry()
