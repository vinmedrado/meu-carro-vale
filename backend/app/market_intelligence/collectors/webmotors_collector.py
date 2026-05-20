from app.market_intelligence.collectors.base_collector import BaseCollector, CollectionRequest, CollectionResult

class WebmotorsCollector(BaseCollector):
    source = "webmotors"
    base_url = "https://webmotors.com.br"
    enabled = False

    def collect(self, request: CollectionRequest) -> CollectionResult:
        return CollectionResult(self.source, False, [], "Coletor responsável criado em modo plugável. Ative somente com API/ToS/robots permitidos.")
