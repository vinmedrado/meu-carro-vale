from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from hashlib import sha1
from app.market_intelligence.normalizers.vehicle_normalizer import clean_text


@dataclass
class DuplicateDecision:
    duplicate_score: int
    fingerprint: str
    reason: str


def listing_fingerprint(payload: dict) -> str:
    stable = "|".join(str(payload.get(k, "")) for k in ["source", "brand", "model", "version", "year", "mileage", "state", "price"])
    return sha1(stable.encode("utf-8")).hexdigest()


def duplicate_score(left: dict, right: dict) -> DuplicateDecision:
    title_ratio = SequenceMatcher(None, clean_text(left.get("title", "")), clean_text(right.get("title", ""))).ratio()
    price_delta = abs(float(left.get("price") or 0) - float(right.get("price") or 0)) / max(float(left.get("price") or 1), 1)
    km_delta = abs(int(left.get("mileage") or 0) - int(right.get("mileage") or 0))
    same_core = all(str(left.get(k, "")).lower() == str(right.get(k, "")).lower() for k in ["brand", "model", "year", "state"])
    score = 0
    score += 35 if same_core else 0
    score += int(title_ratio * 30)
    score += 20 if price_delta <= .015 else 12 if price_delta <= .04 else 0
    score += 15 if km_delta <= 1000 else 8 if km_delta <= 5000 else 0
    reason = "provável repostagem/clonagem" if score >= 82 else "possível similaridade" if score >= 65 else "distinto"
    return DuplicateDecision(min(100, score), listing_fingerprint(left), reason)
