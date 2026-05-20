from __future__ import annotations
import time
from dataclasses import dataclass
from typing import Any, Iterable
import httpx
from config.settings import get_settings


@dataclass
class CollectionResult:
    source: str
    records: list[dict[str, Any]]
    errors: list[str]


class ResponsibleHttpClient:
    def __init__(self):
        self.settings = get_settings()
        self._last_request = 0.0
        self.client = httpx.Client(headers={"User-Agent": self.settings.user_agent}, timeout=30)

    def get_json(self, url: str) -> Any:
        elapsed = time.monotonic() - self._last_request
        delay = self.settings.safe_delay_seconds
        if elapsed < delay:
            time.sleep(delay - elapsed)
        response = self.client.get(url)
        self._last_request = time.monotonic()
        response.raise_for_status()
        return response.json()


class BaseCollector:
    source = "base"
    enabled = False

    def collect(self, **kwargs) -> CollectionResult:
        raise NotImplementedError


class PreparedMarketplaceCollector(BaseCollector):
    enabled = False
    robots_policy_required = True

    def collect(self, **kwargs) -> CollectionResult:
        return CollectionResult(
            source=self.source,
            records=[],
            errors=[f"Coletor {self.source} preparado, mas desabilitado por segurança/termos de uso."],
        )
