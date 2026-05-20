from __future__ import annotations
from dataclasses import dataclass
from .catalog_normalizer import normalize_text, similarity

@dataclass
class DedupDecision:
    is_duplicate: bool
    confidence: float
    reason: str


def brand_key(vehicle_type: str, fipe_brand_code: str | int | None) -> tuple[str, str]:
    return str(vehicle_type), str(fipe_brand_code or "")


def model_key(vehicle_type: str, brand_id: int, fipe_model_code: str | int | None) -> tuple[str, int, str]:
    return str(vehicle_type), int(brand_id), str(fipe_model_code or "")


def version_key(vehicle_type: str, model_id: int, fipe_year_code: str | int | None, fipe_code: str | None) -> tuple[str, int, str, str]:
    return str(vehicle_type), int(model_id), str(fipe_year_code or ""), str(fipe_code or "")


def fuzzy_duplicate(name_a: str | None, name_b: str | None, threshold: float = 0.94) -> DedupDecision:
    if normalize_text(name_a) == normalize_text(name_b):
        return DedupDecision(True, 1.0, "Nome normalizado idêntico")
    score = similarity(name_a, name_b)
    return DedupDecision(score >= threshold, round(score, 3), "Similaridade textual alta" if score >= threshold else "Nomes distintos")
