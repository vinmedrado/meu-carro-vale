from __future__ import annotations
import re
import unicodedata
from difflib import get_close_matches
from hashlib import sha256
from typing import Any

FIELD_ALIASES = {
    "brand": "marca", "marca": "marca",
    "model": "modelo", "modelo": "modelo",
    "version": "versao", "versão": "versao", "versao": "versao",
    "year": "ano", "ano": "ano", "ano_modelo": "ano",
    "mileage": "km", "quilometragem": "km", "km": "km", "odometro": "km",
    "price": "preco", "preço": "preco", "preco": "preco", "valor": "preco",
    "city": "cidade", "cidade": "cidade", "municipio": "cidade",
    "state": "estado", "uf": "estado", "estado": "estado",
    "source": "fonte", "fonte": "fonte", "origem": "fonte",
    "url": "url", "link": "url",
    "fuel": "combustivel", "combustível": "combustivel", "combustivel": "combustivel",
    "transmission": "cambio", "câmbio": "cambio", "cambio": "cambio",
    "color": "cor", "cor": "cor",
    "seller_type": "vendedor_tipo", "vendedor_tipo": "vendedor_tipo", "tipo_vendedor": "vendedor_tipo",
    "published_at": "data_publicacao", "data_publicacao": "data_publicacao",
    "plate": "placa_parcial", "placa": "placa_parcial", "placa_parcial": "placa_parcial",
    "seller_id": "vendedor_id", "vendedor_id": "vendedor_id",
}

BRAND_ALIASES = {
    "Vw": "Volkswagen", "Volks": "Volkswagen", "Mercedez": "Mercedes-Benz", "Mercedes Benz": "Mercedes-Benz",
    "Gm": "Chevrolet", "General Motors": "Chevrolet", "Citroen": "Citroën", "Peugeot Citroen": "Peugeot",
}
MODEL_ALIASES = {
    "Corolla Xei": ("Toyota", "Corolla", "XEI"),
    "Corolla Xei 2.0": ("Toyota", "Corolla", "XEI 2.0"),
    "Corolla Xei Flex Cvt": ("Toyota", "Corolla", "XEI 2.0 Flex CVT"),
    "Onix Plus": ("Chevrolet", "Onix Plus", None),
    "Hr-V": ("Honda", "HR-V", None),
    "Hrv": ("Honda", "HR-V", None),
    "T-Cross": ("Volkswagen", "T-Cross", None),
    "T Cross": ("Volkswagen", "T-Cross", None),
}
FUEL_ALIASES = {"Flexfuel": "Flex", "Alcool/Gasolina": "Flex", "Gasolina E Alcool": "Flex", "Elétrico": "Eletrico"}
TRANSMISSION_ALIASES = {"Automatico": "Automático", "Automatica": "Automático", "Aut": "Automático", "Cvt": "CVT", "Manual 6 Marchas": "Manual"}

KNOWN_MODELS = sorted(set(v[1] for v in MODEL_ALIASES.values()) | {"Corolla", "Civic", "Onix", "Onix Plus", "HB20", "Tracker", "Compass", "T-Cross", "HR-V", "Creta"})


def strip_accents(value: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", value) if not unicodedata.combining(c))


def compact_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", strip_accents(str(value or "")).lower())


def clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = strip_accents(str(value)).strip()
    text = re.sub(r"\s+", " ", text)
    return text.title() if text else None


def normalize_money(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace("R$", "").replace(".", "").replace(",", ".")
    text = re.sub(r"[^0-9.]", "", text)
    return float(text) if text else None


def normalize_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    text = re.sub(r"[^0-9]", "", str(value))
    return int(text) if text else None


def normalize_alias(value: str | None, aliases: dict[str, str]) -> str | None:
    if not value:
        return value
    key = compact_key(value)
    for alias, normalized in aliases.items():
        if compact_key(alias) == key:
            return normalized
    return value


class VehicleNormalizer:
    def normalize(self, record: dict[str, Any]) -> dict[str, Any]:
        mapped: dict[str, Any] = {}
        for key, value in record.items():
            mapped[FIELD_ALIASES.get(str(key).lower().strip(), str(key).lower().strip())] = value

        marca = normalize_alias(clean_text(mapped.get("marca")), BRAND_ALIASES)
        modelo = clean_text(mapped.get("modelo"))
        versao = clean_text(mapped.get("versao"))

        alias_key = " ".join(x for x in [modelo, versao] if x)
        matched_alias = self._match_model_alias(alias_key) or self._match_model_alias(modelo)
        if matched_alias:
            alias_brand, alias_model, alias_version = matched_alias
            marca = marca or alias_brand
            modelo = alias_model
            if alias_version and not versao:
                versao = alias_version

        modelo = self._normalize_model(modelo)
        versao = self._normalize_version(versao)
        normalized = {
            "marca": marca,
            "modelo": modelo,
            "versao": versao,
            "ano": normalize_int(mapped.get("ano")),
            "km": normalize_int(mapped.get("km")),
            "preco": normalize_money(mapped.get("preco")),
            "cidade": clean_text(mapped.get("cidade")),
            "estado": (clean_text(mapped.get("estado")) or "")[:2].upper() or None,
            "fonte": clean_text(mapped.get("fonte")) or "Importado",
            "url": mapped.get("url"),
            "vendedor_tipo": clean_text(mapped.get("vendedor_tipo")),
            "cambio": normalize_alias(clean_text(mapped.get("cambio")), TRANSMISSION_ALIASES),
            "combustivel": normalize_alias(clean_text(mapped.get("combustivel")), FUEL_ALIASES),
            "cor": clean_text(mapped.get("cor")),
            "normalizado": True,
            "placa_parcial": clean_text(mapped.get("placa_parcial")),
            "vendedor_id": clean_text(mapped.get("vendedor_id")),
        }
        normalized["qualidade_dado"] = self.quality_score(normalized)
        normalized["hash_similaridade"] = self.similarity_hash(normalized)
        return normalized

    def _match_model_alias(self, value: str | None) -> tuple[str, str, str | None] | None:
        if not value:
            return None
        key = compact_key(value)
        for alias, normalized in MODEL_ALIASES.items():
            if compact_key(alias) == key:
                return normalized
        return None

    def _normalize_model(self, modelo: str | None) -> str | None:
        if not modelo:
            return modelo
        matches = get_close_matches(modelo, KNOWN_MODELS, n=1, cutoff=0.86)
        return matches[0] if matches else modelo

    def _normalize_version(self, versao: str | None) -> str | None:
        if not versao:
            return versao
        text = versao.upper().replace("AUTOMATICO", "AUTOMÁTICO").replace("FLEXFUEL", "FLEX")
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def quality_score(self, record: dict[str, Any]) -> float:
        required = ["marca", "modelo", "ano", "preco", "estado"]
        useful = ["versao", "km", "cidade", "combustivel", "cambio", "url", "vendedor_tipo"]
        score = sum(1 for f in required if record.get(f)) / len(required) * 0.68
        score += sum(1 for f in useful if record.get(f)) / len(useful) * 0.32
        return round(min(score, 1.0), 3)

    def similarity_hash(self, record: dict[str, Any]) -> str:
        base = "|".join(str(record.get(k) or "").lower() for k in ["marca", "modelo", "versao", "ano", "km", "estado", "placa_parcial"])
        return sha256(base.encode("utf-8")).hexdigest()
