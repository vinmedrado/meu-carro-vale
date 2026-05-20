from app.market_intelligence.collectors.base_collector import BaseCollector, CollectionRequest, CollectionResult

class IcarrosCollector(BaseCollector):
    source = "icarros"
    base_url = "https://icarros.com.br"
    enabled = False

    def collect(self, request: CollectionRequest) -> CollectionResult:
        return CollectionResult(self.source, False, [], "Coletor responsável criado em modo plugável. Ative somente com API/ToS/robots permitidos.")
