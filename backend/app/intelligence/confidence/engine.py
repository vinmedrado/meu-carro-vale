from __future__ import annotations

from typing import Any


class ConfidenceEngine:
    def analyze(self, comparables: dict[str, Any], liquidity: dict[str, Any], base_valuation: dict[str, Any]) -> dict[str, Any]:
        count = int(comparables.get("comparables_used") or 0)
        similarity = float(comparables.get("similarity_score") or 0)
        dispersion = float(comparables.get("price_dispersion_index") or .65)
        has_fipe = bool(base_valuation.get("fipe_real") or base_valuation.get("fipe_simulated"))
        regional = float(comparables.get("regional_similarity") or 0)
        score = min(30, count * 3.5) + min(24, max(0, similarity - 55) * .72) + max(0, 22 - dispersion * 46) + (12 if has_fipe else 0) + min(8, regional / 12.5) + min(4, int(liquidity.get("demand_index") or 0) / 25)
        score = int(max(12, min(100, score)))
        level = "Alta" if score >= 76 else "Média" if score >= 52 else "Baixa"
        reasons = []
        if count >= 10: reasons.append("boa quantidade de comparáveis")
        elif count: reasons.append("amostra útil, porém limitada")
        else: reasons.append("sem comparáveis reais suficientes")
        if dispersion <= .12: reasons.append("baixa dispersão de preços")
        elif dispersion >= .28: reasons.append("preços de mercado dispersos")
        if regional >= 80: reasons.append("boa aderência regional")
        return {"confidence_level": level, "confidence_score": score, "confidence_reason": ", ".join(reasons), "analysis_quality": "robusta" if score >= 76 else "moderada" if score >= 52 else "exploratória"}
