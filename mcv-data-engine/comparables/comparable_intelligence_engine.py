from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime
from difflib import SequenceMatcher
from statistics import median
from typing import Any


QUALITY_LABELS = [
    (85, "Excelente"),
    (70, "Bom"),
    (55, "Médio"),
    (0, "Fraco"),
]


@dataclass(slots=True)
class ComparableStats:
    quantidade_comparaveis: int
    preco_minimo: float | None
    preco_mediano: float | None
    preco_maximo: float | None
    preco_p25: float | None
    preco_p75: float | None
    dispersao: float | None
    confianca_amostra: str


class ComparableIntelligenceEngine:
    """Motor de comparáveis para valuation automotivo.

    A engine não inventa tendência: ela calcula similaridade e estatísticas usando
    apenas os anúncios recebidos/persistidos. A saída é própria para alimentar o
    Meu Carro Vale com explicabilidade, impacto de preço e confiança da amostra.
    """

    def __init__(self, min_score: float = 55.0):
        self.min_score = min_score

    def find_comparables(
        self,
        target: dict[str, Any],
        candidates: list[dict[str, Any]],
        limit: int = 30,
        remove_outliers: bool = True,
    ) -> dict[str, Any]:
        scored: list[dict[str, Any]] = []
        target_id = self._record_id(target)
        for candidate in candidates:
            if self._record_id(candidate) == target_id:
                continue
            score_details = self.score(target, candidate)
            if score_details["comparable_score"] < self.min_score:
                continue
            row = {
                **candidate,
                "vehicle_id": target_id,
                "comparable_id": self._record_id(candidate),
                **score_details,
            }
            scored.append(row)

        filtered = self._remove_price_outliers(scored) if remove_outliers else scored
        filtered = sorted(
            filtered,
            key=lambda x: (x.get("comparable_score") or 0, x.get("qualidade_dado") or 0),
            reverse=True,
        )[: max(limit, 1)]
        return {
            "comparables": filtered,
            "sample_statistics": self.sample_statistics(filtered),
            "outliers_removed": max(len(scored) - len(filtered), 0),
        }

    def build_dataset(self, records: list[dict[str, Any]], limit_per_vehicle: int = 10) -> list[dict[str, Any]]:
        clean = [r for r in records if not r.get("duplicado") and r.get("preco") is not None and r.get("ano") is not None]
        dataset: list[dict[str, Any]] = []
        for target in clean:
            candidates = self._candidate_pool(target, clean)
            result = self.find_comparables(target, candidates, limit=limit_per_vehicle)
            for comparable in result["comparables"]:
                dataset.append(self._export_row(target, comparable))
        return dataset

    def score(self, target: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
        brand_model = self._brand_model_similarity(target, candidate) * 35
        version = self._version_similarity(target.get("versao"), candidate.get("versao")) * 20
        year = self._year_similarity(target.get("ano"), candidate.get("ano")) * 15
        km = self._km_similarity(target.get("km"), candidate.get("km")) * 15
        region = self._regional_similarity(target, candidate) * 10
        quality_recency = self._quality_recency(candidate) * 5
        score = round(brand_model + version + year + km + region + quality_recency, 2)
        price_delta = self._number(candidate.get("preco")) - self._number(target.get("preco")) if target.get("preco") is not None and candidate.get("preco") is not None else None
        km_delta = self._safe_delta(candidate.get("km"), target.get("km"))
        year_delta = self._safe_delta(candidate.get("ano"), target.get("ano"))
        regional_match = self._regional_similarity(target, candidate) >= 0.75
        return {
            "comparable_score": score,
            "score": score,
            "match_quality": self._match_quality(score),
            "price_delta": round(price_delta, 2) if price_delta is not None else None,
            "km_delta": int(km_delta) if km_delta is not None else None,
            "year_delta": int(year_delta) if year_delta is not None else None,
            "regional_match": regional_match,
            "similaridade_marca_modelo": round(brand_model / 35, 3),
            "similaridade_versao": round(version / 20, 3),
            "similaridade_ano": round(year / 15, 3),
            "similaridade_km": round(km / 15, 3),
            "similaridade_regional": round(region / 10, 3),
            "price_impact": self._price_impact(target, candidate, price_delta),
            "explanation": self._explain(target, candidate, score, km_delta, year_delta, regional_match),
        }

    def sample_statistics(self, comparables: list[dict[str, Any]]) -> dict[str, Any]:
        prices = sorted(float(c["preco"]) for c in comparables if c.get("preco") is not None)
        if not prices:
            return asdict(ComparableStats(0, None, None, None, None, None, None, "Baixa"))
        p25 = self._quantile(prices, 0.25)
        p75 = self._quantile(prices, 0.75)
        med = median(prices)
        dispersion = round((p75 - p25) / med, 4) if med else None
        avg_score = sum(float(c.get("comparable_score") or 0) for c in comparables) / max(len(comparables), 1)
        confidence = self._sample_confidence(len(comparables), avg_score, dispersion)
        return asdict(ComparableStats(
            quantidade_comparaveis=len(comparables),
            preco_minimo=round(min(prices), 2),
            preco_mediano=round(float(med), 2),
            preco_maximo=round(max(prices), 2),
            preco_p25=round(p25, 2),
            preco_p75=round(p75, 2),
            dispersao=dispersion,
            confianca_amostra=confidence,
        ))

    def _candidate_pool(self, target: dict[str, Any], records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        brand = self._key(target.get("marca"))
        model = self._key(target.get("modelo"))
        year = self._number(target.get("ano"))
        pool = []
        for row in records:
            if self._record_id(row) == self._record_id(target):
                continue
            if brand and self._key(row.get("marca")) != brand:
                continue
            if model and self._key(row.get("modelo")) != model:
                continue
            if year and row.get("ano") is not None and abs(self._number(row.get("ano")) - year) > 2:
                continue
            pool.append(row)
        return pool

    def _export_row(self, target: dict[str, Any], comparable: dict[str, Any]) -> dict[str, Any]:
        return {
            "vehicle_id": comparable.get("vehicle_id") or self._record_id(target),
            "comparable_id": comparable.get("comparable_id") or self._record_id(comparable),
            "marca": target.get("marca"),
            "modelo": target.get("modelo"),
            "versao": target.get("versao"),
            "ano": target.get("ano"),
            "estado": target.get("estado"),
            "cidade": target.get("cidade"),
            "preco_base": target.get("preco"),
            "preco_comparavel": comparable.get("preco"),
            "km_base": target.get("km"),
            "km_comparavel": comparable.get("km"),
            "score": comparable.get("comparable_score"),
            "comparable_score": comparable.get("comparable_score"),
            "match_quality": comparable.get("match_quality"),
            "price_delta": comparable.get("price_delta"),
            "km_delta": comparable.get("km_delta"),
            "year_delta": comparable.get("year_delta"),
            "regional_match": comparable.get("regional_match"),
            "explanation": comparable.get("explanation"),
            "price_impact": comparable.get("price_impact"),
            "fonte": comparable.get("fonte"),
            "url": comparable.get("url"),
        }

    def _brand_model_similarity(self, target: dict[str, Any], candidate: dict[str, Any]) -> float:
        brand = 1.0 if self._key(target.get("marca")) == self._key(candidate.get("marca")) else self._ratio(target.get("marca"), candidate.get("marca"))
        model = 1.0 if self._key(target.get("modelo")) == self._key(candidate.get("modelo")) else self._ratio(target.get("modelo"), candidate.get("modelo"))
        return max(0.0, min(1.0, brand * 0.45 + model * 0.55))

    def _version_similarity(self, a: Any, b: Any) -> float:
        if not a and not b:
            return 0.65
        if not a or not b:
            return 0.35
        ratio = self._ratio(a, b)
        tokens_a = set(self._key(a).split())
        tokens_b = set(self._key(b).split())
        overlap = len(tokens_a & tokens_b) / max(len(tokens_a | tokens_b), 1) if tokens_a or tokens_b else 0
        return max(ratio, overlap)

    def _year_similarity(self, a: Any, b: Any) -> float:
        if a is None or b is None:
            return 0.45
        diff = abs(self._number(a) - self._number(b))
        if diff == 0:
            return 1.0
        if diff == 1:
            return 0.82
        if diff == 2:
            return 0.58
        return max(0.0, 0.35 - diff * 0.05)

    def _km_similarity(self, a: Any, b: Any) -> float:
        if a is None or b is None:
            return 0.45
        a_num, b_num = self._number(a), self._number(b)
        diff = abs(a_num - b_num)
        base = max(a_num, b_num, 1)
        pct = diff / base
        if diff <= 5_000:
            return 1.0
        if diff <= 15_000:
            return 0.82
        if pct <= 0.30:
            return 0.66
        if pct <= 0.50:
            return 0.48
        return 0.25

    def _regional_similarity(self, target: dict[str, Any], candidate: dict[str, Any]) -> float:
        if target.get("cidade") and candidate.get("cidade") and self._key(target.get("cidade")) == self._key(candidate.get("cidade")):
            return 1.0
        if target.get("estado") and candidate.get("estado") and str(target.get("estado")).upper() == str(candidate.get("estado")).upper():
            return 0.78
        return 0.35

    def _quality_recency(self, candidate: dict[str, Any]) -> float:
        quality = float(candidate.get("qualidade_dado") or 0.55)
        recency = self._recency_score(candidate.get("data_coleta") or candidate.get("data_publicacao"))
        return max(0.0, min(1.0, quality * 0.65 + recency * 0.35))

    def _recency_score(self, value: Any) -> float:
        if not value:
            return 0.55
        try:
            if isinstance(value, datetime):
                dt = value.date()
            elif isinstance(value, date):
                dt = value
            else:
                dt = datetime.fromisoformat(str(value).replace("Z", "").split("+")[0]).date()
            days = (date.today() - dt).days
        except Exception:
            return 0.55
        if days <= 7:
            return 1.0
        if days <= 30:
            return 0.85
        if days <= 90:
            return 0.65
        return 0.40

    def _price_impact(self, target: dict[str, Any], candidate: dict[str, Any], price_delta: float | None) -> str:
        if price_delta is None:
            return "neutro"
        km_delta = self._safe_delta(candidate.get("km"), target.get("km"))
        if price_delta >= 0 and km_delta is not None and km_delta > 8_000:
            return "pressiona preço para cima"
        if price_delta <= 0 and km_delta is not None and km_delta < -8_000:
            return "pressiona preço para baixo"
        if price_delta > (float(target.get("preco") or 0) * 0.06):
            return "pressiona preço para cima"
        if price_delta < -(float(target.get("preco") or 0) * 0.06):
            return "pressiona preço para baixo"
        return "neutro"

    def _explain(self, target: dict[str, Any], candidate: dict[str, Any], score: float, km_delta: float | None, year_delta: float | None, regional_match: bool) -> str:
        parts: list[str] = []
        if self._key(target.get("marca")) == self._key(candidate.get("marca")) and self._key(target.get("modelo")) == self._key(candidate.get("modelo")):
            parts.append("mesma marca e modelo")
        else:
            parts.append("modelo semelhante")
        if self._version_similarity(target.get("versao"), candidate.get("versao")) >= 0.82:
            parts.append("versão compatível")
        elif target.get("versao") and candidate.get("versao"):
            parts.append("versão diferente, usada com peso reduzido")
        if year_delta is not None:
            parts.append("mesmo ano" if year_delta == 0 else f"ano com diferença de {abs(int(year_delta))}")
        if km_delta is not None:
            if abs(km_delta) <= 10_000:
                parts.append("quilometragem semelhante")
            elif km_delta > 0:
                parts.append("quilometragem maior que a base")
            else:
                parts.append("quilometragem menor que a base")
        parts.append("região compatível" if regional_match else "região diferente, peso regional menor")
        quality = self._match_quality(score).lower()
        return f"Comparável {quality}: " + ", ".join(parts) + "."

    def _remove_price_outliers(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        prices = sorted(float(r["preco"]) for r in rows if r.get("preco") is not None)
        if len(prices) < 5:
            return rows
        q1 = self._quantile(prices, 0.25)
        q3 = self._quantile(prices, 0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        return [r for r in rows if r.get("preco") is None or lower <= float(r["preco"]) <= upper]

    def _sample_confidence(self, count: int, avg_score: float, dispersion: float | None) -> str:
        dispersion = 1.0 if dispersion is None else dispersion
        if count >= 12 and avg_score >= 78 and dispersion <= 0.16:
            return "Alta"
        if count >= 6 and avg_score >= 68 and dispersion <= 0.24:
            return "Média"
        return "Baixa"

    def _match_quality(self, score: float) -> str:
        for threshold, label in QUALITY_LABELS:
            if score >= threshold:
                return label
        return "Fraco"

    def _quantile(self, values: list[float], q: float) -> float:
        if not values:
            return 0.0
        pos = (len(values) - 1) * q
        lower = int(pos)
        upper = min(lower + 1, len(values) - 1)
        weight = pos - lower
        return values[lower] * (1 - weight) + values[upper] * weight

    def _record_id(self, record: dict[str, Any]) -> str:
        if record.get("id") is not None:
            return str(record["id"])
        from hashlib import sha256
        key = "|".join(str(record.get(k) or "") for k in ["url", "marca", "modelo", "versao", "ano", "km", "preco", "cidade", "estado"])
        return sha256(key.encode("utf-8")).hexdigest()[:16]

    def _ratio(self, a: Any, b: Any) -> float:
        return SequenceMatcher(None, self._key(a), self._key(b)).ratio()

    def _key(self, value: Any) -> str:
        import re
        import unicodedata
        text = unicodedata.normalize("NFKD", str(value or "").lower())
        text = "".join(ch for ch in text if not unicodedata.combining(ch))
        text = re.sub(r"[^a-z0-9]+", " ", text).strip()
        return text

    def _number(self, value: Any) -> float:
        return float(value or 0)

    def _safe_delta(self, a: Any, b: Any) -> float | None:
        if a is None or b is None:
            return None
        return self._number(a) - self._number(b)
