from __future__ import annotations
import re
import unicodedata
from difflib import SequenceMatcher

BRAND_ALIASES = {
    "gm": "chevrolet",
    "general motors": "chevrolet",
    "chevy": "chevrolet",
    "vw": "volkswagen",
    "volks": "volkswagen",
    "mercedes": "mercedes-benz",
    "mb": "mercedes-benz",
    "range rover": "land rover",
    "hoda": "honda",
    "hiunday": "hyundai",
}

MODEL_ALIASES = {
    "s 10": "s10",
    "s-10": "s10",
    "hrv": "hr-v",
    "hr v": "hr-v",
    "tcross": "t-cross",
    "t cross": "t-cross",
    "corsa classic": "classic",
    "onix sedan": "onix plus",
}

POPULAR_VERSION_ALIASES = {
    "agile ltz": "agile ltz",
    "agile lt": "agile lt",
    "agile effect": "agile effect",
    "classic": "classic",
    "prisma": "prisma",
}


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    text = text.lower().replace("/", " ").replace("_", " ")
    text = re.sub(r"[^a-z0-9\-\. ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def canonical_brand(name: str | None) -> str:
    normalized = normalize_text(name)
    normalized = BRAND_ALIASES.get(normalized, normalized)
    names = {"chevrolet": "Chevrolet", "volkswagen": "Volkswagen", "mercedes-benz": "Mercedes-Benz", "land rover": "Land Rover", "honda": "Honda", "hyundai": "Hyundai"}
    return names.get(normalized, str(name or "").strip() or normalized.title())


def canonical_model(name: str | None) -> str:
    normalized = normalize_text(name)
    normalized = MODEL_ALIASES.get(normalized, normalized)
    return normalized.upper() if normalized in {"s10"} else normalized.title()


def canonical_version(name: str | None) -> str:
    normalized = normalize_text(name)
    normalized = POPULAR_VERSION_ALIASES.get(normalized, normalized)
    return normalized.upper() if any(tok in normalized.split() for tok in ["lt", "ltz"]) else normalized.title()


def similarity(a: str | None, b: str | None) -> float:
    return SequenceMatcher(None, normalize_text(a), normalize_text(b)).ratio()
