from __future__ import annotations

import json
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen

from sqlalchemy.orm import Session
from app.models.market import FipePrice
from app.services.normalization import normalize_brand, normalize_model, parse_price

VEHICLE_TYPES = {"carros", "motos", "caminhoes"}


@dataclass
class TTLCacheItem:
    expires_at: float
    data: Any


class SimpleTTLCache:
    def __init__(self, ttl_seconds: int = 60 * 60 * 12):
        self.ttl_seconds = ttl_seconds
        self._items: dict[str, TTLCacheItem] = {}

    def get(self, key: str) -> Any | None:
        item = self._items.get(key)
        if not item or item.expires_at < time.time():
            self._items.pop(key, None)
            return None
        return item.data

    def set(self, key: str, data: Any) -> None:
        self._items[key] = TTLCacheItem(expires_at=time.time() + self.ttl_seconds, data=data)


class FipeService:
    """Integração real com a Tabela FIPE via API pública Parallelum.

    Não é usada para simular preço. No APP_MODE=REAL, quando a API não responde e
    não existe cache local, o valuation informa baixa disponibilidade de dados em vez
    de inventar valor principal.
    """

    def __init__(self, ttl_seconds: int = 60 * 60 * 12):
        self.base_url = "https://parallelum.com.br/fipe/api/v1"
        self.cache = _shared_cache(ttl_seconds)

    def _vehicle_type(self, vehicle_type: str) -> str:
        normalized = (vehicle_type or "carros").lower().strip()
        if normalized not in VEHICLE_TYPES:
            raise ValueError("tipo de veículo inválido")
        return normalized

    def _get_json(self, path: str) -> Any:
        key = path
        cached = self.cache.get(key)
        if cached is not None:
            return cached
        url = f"{self.base_url}{path}"
        request = Request(url, headers={"User-Agent": "Meu Carro ValeAI/1.0 (+portfolio demo)"})
        with urlopen(request, timeout=12) as response:
            data = json.loads(response.read().decode("utf-8"))
        self.cache.set(key, data)
        return data

    def brands(self, vehicle_type: str = "carros") -> list[dict[str, str]]:
        vt = self._vehicle_type(vehicle_type)
        rows = self._get_json(f"/{vt}/marcas")
        return [{"code": str(item.get("codigo", "")), "name": item.get("nome", "")} for item in rows]

    def models(self, vehicle_type: str, brand_code: str) -> list[dict[str, str]]:
        vt = self._vehicle_type(vehicle_type)
        data = self._get_json(f"/{vt}/marcas/{quote(str(brand_code))}/modelos")
        rows = data.get("modelos", []) if isinstance(data, dict) else []
        return [{"code": str(item.get("codigo", "")), "name": item.get("nome", "")} for item in rows]

    def years(self, vehicle_type: str, brand_code: str, model_code: str) -> list[dict[str, str]]:
        vt = self._vehicle_type(vehicle_type)
        rows = self._get_json(f"/{vt}/marcas/{quote(str(brand_code))}/modelos/{quote(str(model_code))}/anos")
        return [{"code": str(item.get("codigo", "")), "name": item.get("nome", "")} for item in rows]

    def price(self, db: Session, vehicle_type: str, brand_code: str, model_code: str, year_code: str) -> dict[str, Any]:
        vt = self._vehicle_type(vehicle_type)
        data = self._get_json(
            f"/{vt}/marcas/{quote(str(brand_code))}/modelos/{quote(str(model_code))}/anos/{quote(str(year_code))}"
        )
        normalized = self.normalize_price(vt, data)
        self.save_price(db, normalized, data)
        return normalized

    def normalize_price(self, vehicle_type: str, data: dict[str, Any]) -> dict[str, Any]:
        raw_year = str(data.get("AnoModelo") or "0")
        return {
            "vehicle_type": vehicle_type,
            "brand": normalize_brand(data.get("Marca")),
            "model": normalize_model(data.get("Modelo")),
            "year": int(raw_year[:4]) if raw_year[:4].isdigit() else 0,
            "fipe_code": str(data.get("CodigoFipe") or ""),
            "fuel": str(data.get("Combustivel") or ""),
            "reference_month": str(data.get("MesReferencia") or ""),
            "value": parse_price(data.get("Valor")),
        }

    def save_price(self, db: Session, normalized: dict[str, Any], raw: dict[str, Any]) -> None:
        existing = (
            db.query(FipePrice)
            .filter(
                FipePrice.vehicle_type == normalized["vehicle_type"],
                FipePrice.fipe_code == normalized["fipe_code"],
                FipePrice.year == normalized["year"],
                FipePrice.fuel == normalized["fuel"],
            )
            .first()
        )
        if existing:
            existing.value = normalized["value"]
            existing.reference_month = normalized["reference_month"]
            existing.raw = raw
        else:
            db.add(FipePrice(**normalized, raw=raw))
        db.commit()

    def cached_price_for_vehicle(self, db: Session, brand: str, model: str, year: int) -> FipePrice | None:
        brand_norm = normalize_brand(brand)
        model_norm = normalize_model(model)
        return (
            db.query(FipePrice)
            .filter(FipePrice.brand == brand_norm, FipePrice.model.like(f"%{model_norm}%"), FipePrice.year == year)
            .order_by(FipePrice.updated_at.desc())
            .first()
        )


@lru_cache(maxsize=4)
def _shared_cache(ttl_seconds: int) -> SimpleTTLCache:
    return SimpleTTLCache(ttl_seconds=ttl_seconds)
