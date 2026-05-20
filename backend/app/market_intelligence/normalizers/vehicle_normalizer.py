from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, asdict
from difflib import SequenceMatcher
from typing import Any

BRAND_ALIASES = {
    "vw": "volkswagen", "volks": "volkswagen", "chev": "chevrolet", "gm": "chevrolet",
    "mercedes benz": "mercedes-benz", "mercedes": "mercedes-benz", "citroen": "citroën",
}
FUEL_ALIASES = {"flex": "flex", "alcool": "flex", "álcool": "flex", "gasolina": "gasolina", "diesel": "diesel", "eletrico": "elétrico", "hibrido": "híbrido"}
TRANSMISSION_ALIASES = {"aut": "automático", "automatico": "automático", "automática": "automático", "manual": "manual", "cvt": "cvt"}


def strip_accents(value: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", value or "") if not unicodedata.combining(c))


def clean_text(value: str | None) -> str:
    value = strip_accents(value or "").lower().strip()
    value = re.sub(r"[^a-z0-9\s\-/]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def normalize_brand(value: str | None) -> str:
    text = clean_text(value)
    return BRAND_ALIASES.get(text, text)


def normalize_model(value: str | None) -> str:
    text = clean_text(value)
    text = re.sub(r"\b(1\s*0|1\s*4|1\s*6|2\s*0|1\.0|1\.4|1\.6|2\.0|turbo|flex|automatico|manual|cvt)\b", "", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_version(value: str | None) -> str:
    return clean_text(value)


def normalize_fuel(value: str | None) -> str:
    text = clean_text(value)
    for token, normalized in FUEL_ALIASES.items():
        if token in text:
            return normalized
    return text


def normalize_transmission(value: str | None) -> str:
    text = clean_text(value)
    for token, normalized in TRANSMISSION_ALIASES.items():
        if token in text:
            return normalized
    return text


def normalize_state(value: str | None) -> str:
    return (value or "").strip().upper()[:2]


def parse_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    digits = re.sub(r"[^0-9]", "", str(value))
    return int(digits) if digits else default


def parse_price(value: Any) -> float:
    if value is None:
        return 0.0
    text = str(value).replace("R$", "").strip()
    text = re.sub(r"[^0-9,\.]", "", text)
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    elif text.count(".") == 1 and len(text.rsplit(".", 1)[-1]) == 3:
        text = text.replace(".", "")
    try:
        return float(text)
    except ValueError:
        return 0.0


def text_similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, clean_text(left), clean_text(right)).ratio()


@dataclass
class NormalizedListing:
    title: str
    price: float
    brand: str
    model: str
    version: str
    year: int
    mileage: int
    city: str
    state: str
    transmission: str
    fuel: str
    url: str
    source: str
    seller_type: str = ""
    normalized_key: str = ""
    raw: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["raw"] = data.get("raw") or {}
        return data


def normalize_listing(row: dict[str, Any], source: str = "unknown") -> NormalizedListing:
    title = str(row.get("title") or row.get("titulo") or "").strip()
    brand = normalize_brand(row.get("brand") or row.get("marca") or "")
    model = normalize_model(row.get("model") or row.get("modelo") or title)
    version = normalize_version(row.get("version") or row.get("versao") or "")
    year = parse_int(row.get("year") or row.get("ano"))
    mileage = parse_int(row.get("mileage") or row.get("km") or row.get("quilometragem"))
    state = normalize_state(row.get("state") or row.get("uf"))
    city = clean_text(row.get("city") or row.get("cidade") or "").title()
    fuel = normalize_fuel(row.get("fuel") or row.get("combustivel") or "")
    transmission = normalize_transmission(row.get("transmission") or row.get("cambio") or "")
    price = parse_price(row.get("price") or row.get("preco"))
    url = str(row.get("url") or row.get("link") or "").strip()
    seller_type = clean_text(row.get("seller_type") or row.get("vendedor") or "")
    key = "|".join([source, brand, model, version, str(year), str(mileage // 1000), state, str(round(price / 1000))])
    return NormalizedListing(title=title or f"{brand} {model} {year}", price=price, brand=brand, model=model, version=version, year=year, mileage=mileage, city=city, state=state, transmission=transmission, fuel=fuel, url=url, source=source, seller_type=seller_type, normalized_key=key, raw=row)
