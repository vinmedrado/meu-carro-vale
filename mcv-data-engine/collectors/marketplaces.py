from collectors.base import PreparedMarketplaceCollector


class OlxCollector(PreparedMarketplaceCollector):
    source = "OLX"


class WebmotorsCollector(PreparedMarketplaceCollector):
    source = "Webmotors"


class IcarrosCollector(PreparedMarketplaceCollector):
    source = "iCarros"


class MercadoLivreCollector(PreparedMarketplaceCollector):
    source = "Mercado Livre"


class KavakCollector(PreparedMarketplaceCollector):
    source = "Kavak"
