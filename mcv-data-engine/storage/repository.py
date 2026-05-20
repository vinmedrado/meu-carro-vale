from __future__ import annotations
import json
from storage.models import MarketListing, MarketSnapshot, MarketLiquidity, VehicleCatalog, MarketQuality


class Repository:
    def __init__(self, session):
        self.session = session

    def save_listings(self, records: list[dict], batch_size: int = 1000) -> int:
        return self._bulk_save(MarketListing, records, batch_size=batch_size)

    def save_snapshots(self, records: list[dict], batch_size: int = 1000) -> int:
        return self._bulk_save(MarketSnapshot, records, batch_size=batch_size)

    def save_liquidity(self, records: list[dict], batch_size: int = 1000) -> int:
        return self._bulk_save(MarketLiquidity, records, batch_size=batch_size)

    def save_market_quality(self, records: list[dict], batch_size: int = 1000) -> int:
        return self._bulk_save(MarketQuality, records, batch_size=batch_size)

    def save_vehicle_catalog(self, records: list[dict], batch_size: int = 1000) -> int:
        payloads = []
        for r in records:
            payloads.append({
                "marca": r.get("marca") or "",
                "modelo": r.get("modelo") or "",
                "versao": r.get("versao"),
                "ano": r.get("ano"),
                "codigo_fipe": r.get("codigo_fipe"),
                "preco_fipe": r.get("preco") or r.get("preco_fipe"),
                "combustivel": r.get("combustivel"),
                "mes_referencia": r.get("mes_referencia"),
            })
        return self._bulk_save(VehicleCatalog, payloads, batch_size=batch_size)

    def _bulk_save(self, model, records: list[dict], batch_size: int = 1000) -> int:
        if not records:
            return 0
        allowed = {c.name for c in model.__table__.columns if c.name != "id"}
        rows = []
        for r in records:
            row = {k: self._adapt_value(v) for k, v in r.items() if k in allowed}
            rows.append(row)
        for idx in range(0, len(rows), batch_size):
            self.session.bulk_insert_mappings(model, rows[idx: idx + batch_size])
        self.session.commit()
        return len(rows)

    def _adapt_value(self, value):
        if isinstance(value, (list, dict)):
            return json.dumps(value, ensure_ascii=False)
        return value
