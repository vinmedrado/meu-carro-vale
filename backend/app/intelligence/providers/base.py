from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from app.intelligence.schemas.core import NormalizedMarketListing, NormalizedVehicleQuery


class MarketProvider(ABC):
    """Contrato seguro para provedores de mercado.

    Nesta etapa os coletores externos ficam como adaptadores plugáveis. Não há
    scraping agressivo nem bypass de políticas: provedores reais devem usar API,
    CSV autorizado, parceria ou rotina permitida pelos termos de cada origem.
    """

    source_name: str

    @abstractmethod
    def search(self, query: NormalizedVehicleQuery) -> Iterable[NormalizedMarketListing]:
        raise NotImplementedError
