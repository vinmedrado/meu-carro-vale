from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any


UF_SET = {"AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"}


def strip_accents(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def normalize_text(value: Any) -> str:
    text = strip_accents(str(value or "")).lower().strip()
    text = re.sub(r"[^a-z0-9\s\-/]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_brand(value: Any) -> str:
    aliases = {"vw": "volkswagen", "gm": "chevrolet", "mercedes benz": "mercedes"}
    text = normalize_text(value)
    return aliases.get(text, text)


def normalize_model(value: Any) -> str:
    return normalize_text(value)


def normalize_version(value: Any) -> str:
    return normalize_text(value)


def normalize_state(value: Any) -> str:
    uf = strip_accents(str(value or "")).upper().strip()[:2]
    return uf if uf in UF_SET else ""


def parse_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    text = str(value).strip()
    text = re.sub(r"[^0-9-]", "", text)
    if text in {"", "-"}:
        return default
    try:
        return int(text)
    except ValueError:
        return default


def parse_price(value: Any) -> float:
    if value is None:
        return 0.0
    text = str(value).strip()
    if not text:
        return 0.0
    text = re.sub(r"[^0-9,.-]", "", text)
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")
    try:
        return float(Decimal(text))
    except (InvalidOperation, ValueError):
        return 0.0


def normalize_url(value: Any) -> str:
    return str(value or "").strip()


@dataclass
class CleanListing:
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
    normalized_key: str
    raw: dict[str, Any]


def clean_listing(row: dict[str, Any]) -> tuple[CleanListing | None, str | None]:
    title = str(row.get("title") or row.get("titulo") or "").strip()
    brand = normalize_brand(row.get("brand") or row.get("marca"))
    model = normalize_model(row.get("model") or row.get("modelo"))
    version = normalize_version(row.get("version") or row.get("versao") or row.get("versão"))
    price = parse_price(row.get("price") or row.get("preco") or row.get("preço"))
    year = parse_int(row.get("year") or row.get("ano"))
    mileage = parse_int(row.get("mileage") or row.get("km") or row.get("quilometragem"))
    state = normalize_state(row.get("state") or row.get("uf") or row.get("estado"))
    city = str(row.get("city") or row.get("cidade") or "").strip()
    transmission = normalize_text(row.get("transmission") or row.get("cambio") or row.get("câmbio"))
    fuel = normalize_text(row.get("fuel") or row.get("combustivel") or row.get("combustível"))
    url = normalize_url(row.get("url") or row.get("link"))
    source = normalize_text(row.get("source") or row.get("origem") or "csv") or "csv"

    if not brand or not model:
        return None, "marca/modelo ausentes"
    if price <= 0:
        return None, "preço ausente"
    if price < 5_000 or price > 2_500_000:
        return None, "preço fora da faixa aceita"
    if year < 1980 or year > 2036:
        return None, "ano inválido"
    if mileage < 0 or mileage > 1_000_000:
        return None, "km inválida"
    if not title:
        title = f"{brand} {model} {version} {year}".strip()

    approx_title = normalize_text(title)[:120]
    normalized_key = url or f"{brand}|{model}|{version}|{year}|{round(price,-2)}|{round(mileage,-3)}|{city.lower()}|{state}|{approx_title}"
    return CleanListing(
        title=title,
        price=price,
        brand=brand,
        model=model,
        version=version,
        year=year,
        mileage=mileage,
        city=city,
        state=state,
        transmission=transmission,
        fuel=fuel,
        url=url,
        source=source,
        normalized_key=normalized_key,
        raw=row,
    ), None
