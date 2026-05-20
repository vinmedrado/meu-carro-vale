from app.market_intelligence.collectors.base_collector import BaseCollector, CollectionRequest, CollectionResult

class OlxCollector(BaseCollector):
    source = "olx"
    base_url = "https://olx.com.br"
    enabled = False

    def collect(self, request: CollectionRequest) -> CollectionResult:
        return CollectionResult(self.source, False, [], "Coletor responsável criado em modo plugável. Ative somente com API/ToS/robots permitidos.")
