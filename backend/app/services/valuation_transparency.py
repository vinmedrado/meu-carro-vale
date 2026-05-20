from __future__ import annotations

from datetime import datetime, timezone
from statistics import median
from typing import Any


def _money(value: float | int | None) -> int:
    return int(round(float(value or 0) / 100) * 100)


def confidence_explanation(label: str, count: int, regional_count: int, avg_similarity: int, dispersion: float) -> str:
    if label == "Alta":
        return f"Alta confiança porque encontramos {count} anúncios semelhantes, com {regional_count} na mesma região e similaridade média de {avg_similarity}/100. A dispersão entre P25 e P75 está controlada."
    if label == "Média":
        return f"Confiança média: há {count} comparáveis úteis, mas a amostra regional ou a dispersão de preços ainda exige leitura conservadora."
    return f"Baixa confiança: existem poucos comparáveis realmente próximos ou os preços estão muito dispersos para este modelo/região."


def liquidity_explanation(label: str, score: int, regional_count: int) -> str:
    if label in {"Muito Alta", "Alta"}:
        return f"Liquidez {label.lower()}: veículos semelhantes possuem boa procura e volume regional suficiente para sustentar negociação com menor desconto."
    if label == "Média":
        return "Liquidez média: existe procura, mas o tempo de venda pode depender de fotos, histórico, versão e preço inicial."
    return "Liquidez baixa: a amostra indica menor volume ou procura regional, então o preço precisa ser mais defensivo para acelerar a venda."


def market_temperature(dispersion: float, liquidity_score: int, comparable_count: int) -> str:
    if liquidity_score >= 78 and dispersion <= 0.16 and comparable_count >= 8:
        return "Mercado aquecido"
    if dispersion <= 0.22 and comparable_count >= 5:
        return "Mercado estável"
    if dispersion > 0.30:
        return "Mercado disperso"
    return "Mercado em observação"


def build_transparency_payload(
    *,
    vehicle: Any,
    matches: list[Any],
    prices: list[float],
    p25: float,
    p50: float,
    p75: float,
    min_price: float,
    max_price: float,
    fipe_value: float | None,
    ideal: int,
    confidence_score: int,
    confidence_label: str,
    liquidity_score: int,
    liquidity_label: str,
    regional_count: int,
    avg_similarity: int,
    outliers_removed: int,
    weighted_median_value: float,
    market_weight: float = 0.82,
    fipe_weight: float = 0.18,
) -> dict[str, Any]:
    count = len(matches)
    state = str(getattr(vehicle, "state", "") or "").upper()
    year = int(getattr(vehicle, "year", datetime.now().year))
    km = int(getattr(vehicle, "km", 0) or 0)
    dispersion_ratio = round(((p75 - p25) / p50), 3) if p50 else 0
    km_band = {
        "min": max(0, int(km * 0.72)) if km else 0,
        "max": int(km * 1.28) if km else 0,
    }
    price_dispersion = {
        "min": _money(min_price or p25 or ideal),
        "p25": _money(p25 or ideal),
        "p50": _money(p50 or ideal),
        "median": _money(p50 or ideal),
        "p75": _money(p75 or ideal),
        "max": _money(max_price or p75 or ideal),
        "dispersion_ratio": dispersion_ratio,
        "dispersion_label": "Controlada" if dispersion_ratio <= 0.18 else "Moderada" if dispersion_ratio <= 0.30 else "Alta",
    }
    regional_scope = f"{state} e comparáveis nacionais próximos" if state else "Brasil com filtros por similaridade"
    methodology_summary = (
        "Usamos FIPE como referência secundária, anúncios reais semelhantes como principal indicador, removemos preços fora da curva, "
        "calculamos mediana e percentis, ajustamos por região, quilometragem, estado de conservação e liquidez."
    )
    valuation_explanation = (
        f"Esta análise foi baseada em {count} anúncio(s) semelhante(s). "
        f"O mercado real recebeu peso de {round(market_weight * 100)}% e a FIPE peso de {round(fipe_weight * 100)}% quando disponível. "
        f"A faixa considera ano entre {max(year - 1, 1900)} e {year + 1}, quilometragem próxima de {km_band['min']:,} a {km_band['max']:,} km e praça {regional_scope}."
    ).replace(",", ".")
    snapshot_status = market_temperature(dispersion_ratio, liquidity_score, count)
    market_snapshot = {
        "status": snapshot_status,
        "summary": f"{snapshot_status}: {count} comparáveis, liquidez {liquidity_label.lower()} e dispersão {price_dispersion['dispersion_label'].lower()}.",
        "demand": "Alta procura" if liquidity_score >= 78 else "Procura moderada" if liquidity_score >= 55 else "Procura restrita",
        "supply": "Boa oferta regional" if regional_count >= 5 else "Oferta regional limitada",
        "trend": "Faixa estável" if dispersion_ratio <= 0.22 else "Preços variando entre anúncios",
    }
    return {
        "comparables_used": count,
        "comparables_count": count,
        "regional_scope": regional_scope,
        "year_range": [max(year - 1, 1900), year + 1],
        "mileage_range": km_band,
        "average_similarity_score": avg_similarity,
        "outliers_removed": outliers_removed,
        "fipe_weight": round(fipe_weight, 2) if fipe_value else 0,
        "real_market_weight": round(market_weight, 2) if count else 0,
        "weighted_median_price": _money(weighted_median_value),
        "confidence_explanation": confidence_explanation(confidence_label, count, regional_count, avg_similarity, dispersion_ratio),
        "liquidity_explanation": liquidity_explanation(liquidity_label, liquidity_score, regional_count),
        "methodology_summary": methodology_summary,
        "valuation_explanation": valuation_explanation,
        "market_snapshot": market_snapshot,
        "price_dispersion": price_dispersion,
    }
