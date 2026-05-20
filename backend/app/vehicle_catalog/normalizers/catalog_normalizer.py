from __future__ import annotations
import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from app.vehicle_catalog.aliases.brand_aliases import BRAND_ALIASES
from app.vehicle_catalog.aliases.model_aliases import MODEL_ALIASES


def strip_accents(value: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFKD", value or "") if not unicodedata.combining(ch))


def clean_text(value: object) -> str:
    text = strip_accents(str(value or "")).lower().strip()
    text = text.replace("s-10", "s10").replace("h-rv", "hrv").replace("t-cross", "tcross")
    text = re.sub(r"[^a-z0-9\s\-/]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def display_name(value: object) -> str:
    text = str(value or "").strip()
    return re.sub(r"\s+", " ", text)


def normalize_brand_name(value: object) -> str:
    cleaned = clean_text(value).replace("mercedes benz", "mercedes-benz")
    for canonical, aliases in BRAND_ALIASES.items():
        if cleaned == clean_text(canonical) or cleaned in {clean_text(a) for a in aliases}:
            return canonical
    return cleaned


def normalize_model_name(value: object) -> str:
    text = clean_text(value)
    replacements = {"tcross": "t-cross", "hrv": "hr-v", "s10": "s10"}
    for raw, normalized in replacements.items():
        if text == raw:
            return normalized
    text = re.sub(r"\b(hatch|sedan|flex|gasolina|alcool|diesel|automatico|manual|cvt)\b", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def model_alias_index() -> dict[str, tuple[str, str]]:
    index: dict[str, tuple[str, str]] = {}
    for brand, models in MODEL_ALIASES.items():
        for canonical_model, aliases in models.items():
            index[clean_text(canonical_model)] = (brand, canonical_model)
            index[normalize_model_name(canonical_model)] = (brand, canonical_model)
            for alias in aliases:
                index[clean_text(alias)] = (brand, canonical_model)
                index[normalize_model_name(alias)] = (brand, canonical_model)
    return index


def normalize_fuel(value: object) -> str:
    text = clean_text(value)
    if "diesel" in text: return "diesel"
    if "eletr" in text: return "elétrico"
    if "hibr" in text: return "híbrido"
    if "alcool" in text or "gasolina" in text or "flex" in text: return "flex"
    return text


def parse_year(value: object) -> int:
    digits = re.sub(r"[^0-9]", "", str(value or ""))
    return int(digits[:4]) if len(digits) >= 4 else 0


def similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, clean_text(left), clean_text(right)).ratio()


@dataclass
class CatalogMatchResult:
    canonical_brand: str | None
    canonical_model: str | None
    matched_alias: str | None
    confidence_score: int
    match_method: str
    version_hint: str | None = None
