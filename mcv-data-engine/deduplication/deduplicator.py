from __future__ import annotations
from dataclasses import dataclass
from difflib import SequenceMatcher
from hashlib import sha256
from typing import Any


@dataclass(slots=True)
class DeduplicationResult:
    clean_records: list[dict]
    duplicates: list[dict]


def _ratio(a: str | None, b: str | None) -> float:
    return SequenceMatcher(None, (a or "").lower(), (b or "").lower()).ratio()


def _close_number(a: Any, b: Any, percent: float | None = None, absolute: float | None = None) -> bool:
    if a is None or b is None:
        return False
    a, b = float(a), float(b)
    if absolute is not None and abs(a - b) <= absolute:
        return True
    if percent is not None and abs(a - b) / max(abs(a), abs(b), 1) <= percent:
        return True
    return False


class ListingDeduplicator:
    def deduplicate(self, records: list[dict], threshold: float = 0.86) -> DeduplicationResult:
        clean: list[dict] = []
        duplicates: list[dict] = []
        seen_urls: dict[str, int] = {}
        seen_hashes: dict[str, int] = {}

        for record in records:
            url = record.get("url")
            if url and url in seen_urls:
                self._mark_duplicate(record, duplicates, seen_urls[url], "mesma_url", 1.0)
                continue

            h = record.get("hash_similaridade") or self._stable_hash(record)
            if h in seen_hashes:
                self._mark_duplicate(record, duplicates, seen_hashes[h], "mesmo_hash", 1.0)
                continue

            duplicate = self._find_duplicate(record, clean, threshold)
            if duplicate is not None:
                duplicate_index, confidence, reason = duplicate
                self._mark_duplicate(record, duplicates, duplicate_index, reason, confidence)
                continue

            record["duplicado"] = False
            record["duplicate_confidence_score"] = 0.0
            clean.append(record)
            if url:
                seen_urls[url] = len(clean) - 1
            seen_hashes[h] = len(clean) - 1
        return DeduplicationResult(clean, duplicates)

    def _mark_duplicate(self, record: dict, duplicates: list[dict], duplicate_of: int, reason: str, confidence: float) -> None:
        record["duplicado"] = True
        record["duplicate_confidence_score"] = round(confidence, 3)
        duplicates.append({"record": record, "duplicate_of": duplicate_of, "reason": reason, "similarity": round(confidence, 3)})

    def _find_duplicate(self, candidate: dict, clean: list[dict], threshold: float) -> tuple[int, float, str] | None:
        for idx, existing in enumerate(clean):
            confidence, reason = self.duplicate_confidence(candidate, existing)
            if confidence >= threshold:
                return idx, confidence, reason
        return None

    def duplicate_confidence(self, a: dict, b: dict) -> tuple[float, str]:
        if a.get("url") and a.get("url") == b.get("url"):
            return 1.0, "mesma_url"
        if a.get("placa_parcial") and a.get("placa_parcial") == b.get("placa_parcial"):
            return 0.98, "mesma_placa_parcial"
        same_identity = [
            a.get("marca") == b.get("marca"),
            a.get("modelo") == b.get("modelo"),
            a.get("ano") == b.get("ano"),
            a.get("estado") == b.get("estado"),
        ]
        if sum(same_identity) < 3:
            return 0.0, "identidade_distante"
        same_city = bool(a.get("cidade") and a.get("cidade") == b.get("cidade"))
        same_seller = bool(a.get("vendedor_id") and a.get("vendedor_id") == b.get("vendedor_id"))
        # Sem URL, placa, cidade ou vendedor igual, anúncios parecidos podem ser apenas comparáveis.
        if not (same_city or same_seller):
            return 0.0, "comparavel_nao_duplicado"

        version_score = _ratio(a.get("versao"), b.get("versao"))
        city_score = 1.0 if same_city else 0.35
        seller_score = 1.0 if same_seller else 0.35
        price_score = 1.0 if _close_number(a.get("preco"), b.get("preco"), percent=0.025) else 0.25
        km_score = 1.0 if _close_number(a.get("km"), b.get("km"), absolute=1800) else 0.35
        confidence = (
            (sum(same_identity) / 4) * 0.32
            + version_score * 0.16
            + price_score * 0.18
            + km_score * 0.16
            + city_score * 0.09
            + seller_score * 0.09
        )
        # Cidade igual sozinha não basta para considerar duplicado: em marketplaces
        # reais, dois anúncios muito parecidos na mesma cidade podem ser comparáveis
        # válidos. Sem vendedor/placa, reduzimos a confiança para evitar falso positivo.
        if same_city and not same_seller and not a.get("placa_parcial") and not b.get("placa_parcial"):
            confidence *= 0.88
        if confidence >= 0.92:
            reason = "mesmo_veiculo_multiplas_fontes"
        elif confidence >= 0.86:
            reason = "republicacao_provavel"
        else:
            reason = "similaridade_parcial"
        return round(confidence, 3), reason

    def _stable_hash(self, record: dict) -> str:
        base = "|".join(str(record.get(k) or "").lower() for k in ["marca", "modelo", "versao", "ano", "km", "preco", "cidade", "estado"])
        return sha256(base.encode("utf-8")).hexdigest()
