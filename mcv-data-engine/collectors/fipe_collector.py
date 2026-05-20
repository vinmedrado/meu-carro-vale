from __future__ import annotations
from typing import Any
from collectors.base import BaseCollector, CollectionResult, ResponsibleHttpClient
from config.settings import get_settings


class FipeCollector(BaseCollector):
    source = "FIPE"
    enabled = True

    def __init__(self, client: ResponsibleHttpClient | None = None):
        self.client = client or ResponsibleHttpClient()
        self.base_url = get_settings().fipe_base_url.rstrip("/")

    def collect(self, max_brands: int | None = None, max_models_per_brand: int | None = None) -> CollectionResult:
        errors: list[str] = []
        records: list[dict[str, Any]] = []
        try:
            brands = self.client.get_json(f"{self.base_url}/marcas")
            if max_brands:
                brands = brands[:max_brands]
            for brand in brands:
                brand_code = brand.get("codigo")
                brand_name = brand.get("nome")
                try:
                    models_payload = self.client.get_json(f"{self.base_url}/marcas/{brand_code}/modelos")
                    models = models_payload.get("modelos", [])
                    if max_models_per_brand:
                        models = models[:max_models_per_brand]
                    for model in models:
                        model_code = model.get("codigo")
                        years = self.client.get_json(f"{self.base_url}/marcas/{brand_code}/modelos/{model_code}/anos")
                        for year in years:
                            year_code = year.get("codigo")
                            detail = self.client.get_json(
                                f"{self.base_url}/marcas/{brand_code}/modelos/{model_code}/anos/{year_code}"
                            )
                            records.append(self._to_record(brand_name, model.get("nome"), detail))
                except Exception as exc:  # pragma: no cover - network resilience
                    errors.append(f"Falha FIPE marca {brand_name}: {exc}")
        except Exception as exc:  # pragma: no cover - network resilience
            errors.append(f"Falha geral FIPE: {exc}")
        return CollectionResult(source=self.source, records=records, errors=errors)

    def _to_record(self, brand: str | None, model: str | None, detail: dict[str, Any]) -> dict[str, Any]:
        raw_price = str(detail.get("Valor", "")).replace("R$", "").replace(".", "").replace(",", ".").strip()
        price = float(raw_price) if raw_price else None
        model_year = detail.get("AnoModelo")
        return {
            "fonte": self.source,
            "marca": brand or detail.get("Marca"),
            "modelo": model or detail.get("Modelo"),
            "versao": detail.get("Modelo"),
            "ano": int(model_year) if model_year else None,
            "preco": price,
            "combustivel": detail.get("Combustivel"),
            "codigo_fipe": detail.get("CodigoFipe"),
            "mes_referencia": detail.get("MesReferencia"),
        }
