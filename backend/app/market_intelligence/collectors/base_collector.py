from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass
from typing import Any
from urllib import robotparser
from urllib.parse import urlparse

logger = logging.getLogger("meu_carro_vale.market_intelligence")

@dataclass
class CollectionRequest:
    brand: str
    model: str
    year: int | None = None
    state: str | None = None
    limit: int = 50

@dataclass
class CollectionResult:
    source: str
    ok: bool
    rows: list[dict[str, Any]]
    error: str = ""

class BaseCollector:
    source = "base"
    base_url = ""
    enabled = False
    min_interval_seconds = 3.0

    def __init__(self, user_agent: str = "Meu Carro ValeMarketIntel/1.0 (+responsible-rate-limited)") -> None:
        self.user_agent = user_agent
        self._last_call = 0.0

    def is_allowed(self, url: str) -> bool:
        try:
            parsed = urlparse(url)
            rp = robotparser.RobotFileParser(f"{parsed.scheme}://{parsed.netloc}/robots.txt")
            rp.read()
            return rp.can_fetch(self.user_agent, url)
        except Exception as exc:
            logger.warning("robots check failed", extra={"source": self.source, "error": str(exc)})
            return False

    def rate_limit(self) -> None:
        elapsed = time.time() - self._last_call
        wait = self.min_interval_seconds - elapsed
        if wait > 0:
            time.sleep(wait + random.uniform(0, .4))
        self._last_call = time.time()

    def collect(self, request: CollectionRequest) -> CollectionResult:
        if not self.enabled:
            return CollectionResult(self.source, False, [], "Coletor desabilitado até configuração de API/ToS permitida.")
        raise NotImplementedError

    def collect_with_retries(self, request: CollectionRequest, retries: int = 2) -> CollectionResult:
        last_error = ""
        for attempt in range(retries + 1):
            try:
                self.rate_limit()
                return self.collect(request)
            except Exception as exc:
                last_error = str(exc)
                logger.exception("collector failure", extra={"source": self.source, "attempt": attempt})
                time.sleep(2 ** attempt)
        return CollectionResult(self.source, False, [], last_error)
