from __future__ import annotations

import statistics
from datetime import datetime, timezone
from typing import Any
from sqlalchemy.orm import Session
from app.models.market import FipePrice, ValuationComparable, ValuationRun
from app.vehicle_catalog.models import VehicleBrand, VehicleModel, VehicleVersion
from app.services.fipe_service import FipeService
from app.services.valuation_engine import ValuationInput
from app.market_intelligence.analytics.outliers import remove_price_outliers
from app.market_intelligence.comparables.engine import ComparableEngine
from app.market_intelligence.liquidity.liquidity_engine import LiquidityEngine
from app.market_intelligence.normalizers.vehicle_normalizer import normalize_brand, normalize_model, normalize_state
from app.services.valuation_transparency import build_transparency_payload

REGION_MULTIPLIER = {"SP": 1.02, "RJ": 1.01, "MG": 1.0, "PR": 1.0, "SC": 1.01, "RS": .99, "BA": .98, "PE": .98, "GO": 1.0, "DF": 1.01}
CONDITION_FACTOR = {"excelente": 1.035, "bom": 1.0, "regular": .94, "atenção": .89, "atencao": .89}

def round_money(value: float | None) -> int:
    return int(round(float(value or 0) / 100) * 100)

def quantile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    if not ordered: return 0
    idx = (len(ordered) - 1) * q
    lo = int(idx); hi = min(lo + 1, len(ordered) - 1); w = idx - lo
    return ordered[lo] * (1 - w) + ordered[hi] * w

def weighted_median(pairs: list[tuple[float, float]]) -> float:
    pairs = sorted(pairs, key=lambda x: x[0])
    total = sum(w for _, w in pairs) or 1
    acc = 0.0
    for value, weight in pairs:
        acc += weight
        if acc >= total / 2:
            return value
    return pairs[-1][0] if pairs else 0

class ValuationEngineV3:
    def __init__(self, min_comparable_score: int = 62):
        self.comparables = ComparableEngine(min_score=min_comparable_score)
        self.liquidity_engine = LiquidityEngine()
        self.fipe = FipeService()

    def evaluate(self, db: Session, vehicle: ValuationInput, tenant_id: str = "real") -> dict[str, Any]:
        matches = self.comparables.select(db, vehicle)
        fipe_row = self.fipe.cached_price_for_vehicle(db, vehicle.brand, vehicle.model, vehicle.year)
        catalog_version = self._catalog_fipe_version(db, vehicle) if not fipe_row else None
        if not matches and not fipe_row and not catalog_version:
            raise ValueError("APP_MODE=REAL exige FIPE real em cache ou comparáveis reais coletados/importados. Mock não é permitido no cálculo principal real.")
        raw_prices = [float(m.listing.price) for m in matches]
        prices = remove_price_outliers(raw_prices)
        outliers_removed = max(0, len(raw_prices) - len(prices))
        allowed = set(prices)
        matches = [m for m in matches if float(m.listing.price) in allowed] or matches[: min(len(matches), 8)]
        prices = [float(m.listing.price) for m in matches]
        fipe_value = float(fipe_row.value) if fipe_row else (float(catalog_version.fipe_price) if catalog_version else None)
        if prices:
            weighted_pairs = [(m.listing.price, max(.35, m.similarity_score / 100)) for m in matches]
            market_anchor = weighted_median(weighted_pairs)
            p25, p50, p75 = quantile(prices, .25), quantile(prices, .5), quantile(prices, .75)
            trimmed = statistics.mean(sorted(prices)[max(0, int(len(prices)*.1)): max(1, int(len(prices)*.9))]) if len(prices) >= 8 else statistics.mean(prices)
            anchor = market_anchor * .58 + p50 * .25 + trimmed * .17
            if fipe_value:
                anchor = anchor * .82 + fipe_value * .18
        else:
            p25 = p50 = p75 = fipe_value or 0
            anchor = fipe_value or 0
        median_km = statistics.median([m.listing.mileage for m in matches]) if matches else max((2026 - vehicle.year) * 12000, 12000)
        km_factor = self.km_depreciation(vehicle.km, median_km)
        region_factor = REGION_MULTIPLIER.get(normalize_state(vehicle.state), 1.0)
        condition_factor = CONDITION_FACTOR.get(vehicle.condition.lower(), 1.0)
        adjusted = anchor * km_factor * region_factor * condition_factor
        quick = round_money(adjusted * .94); ideal = round_money(adjusted); recommended_top = round_money(adjusted * 1.07)
        regional_count = len([m for m in matches if normalize_state(m.listing.state) == normalize_state(vehicle.state)])
        liquidity = self.liquidity_engine.calculate(prices, regional_count=regional_count)
        avg_similarity = int(statistics.mean([m.similarity_score for m in matches])) if matches else 0
        dispersion = ((p75 - p25) / p50) if p50 else .55
        confidence_score, confidence_label = self.confidence(len(matches), avg_similarity, dispersion, bool(fipe_value), liquidity.score, regional_count)
        min_price = min(prices) if prices else (fipe_value or ideal)
        max_price = max(prices) if prices else (fipe_value or ideal)
        transparency = build_transparency_payload(
            vehicle=vehicle, matches=matches, prices=prices, p25=p25, p50=p50, p75=p75,
            min_price=min_price, max_price=max_price, fipe_value=fipe_value, ideal=ideal,
            confidence_score=confidence_score, confidence_label=confidence_label, liquidity_score=liquidity.score,
            liquidity_label=liquidity.label, regional_count=regional_count, avg_similarity=avg_similarity,
            outliers_removed=outliers_removed, weighted_median_value=market_anchor if prices else 0,
        )
        stats = {"p25": round_money(p25), "p50": round_money(p50), "p75": round_money(p75), "weighted_median": round_money(market_anchor if prices else 0), "count_after_outlier_filter": len(prices), "dispersion": round(dispersion, 3), "outliers_removed": outliers_removed}
        payload = {
            **transparency,
            "mode": "REAL", "data_badge": "Market Intelligence Real", "fipe_real": round_money(fipe_value) if fipe_value else None,
            "fipe_source": "Tabela FIPE via API/cache local/catálogo mestre" if fipe_value else "FIPE não localizada no cache local", "fipe_reference_month": (fipe_row.reference_month if fipe_row else (catalog_version.reference_month if catalog_version else None)),
            "market_reference": ideal, "quick_sale_price": quick, "ideal_price": ideal, "recommended_top_price": recommended_top,
            "negotiation_range": [round_money(quick * .985), round_money(recommended_top * 1.015)], "potential_lost": max(0, ideal - round_money(ideal * .81)),
            "vehicle_score": int(max(40, min(99, liquidity.score * .50 + confidence_score * .30 + (avg_similarity or 65) * .20))),
            "liquidity_score": liquidity.score, "liquidity_label": liquidity.label, "attractiveness_score": liquidity.score,
            "market_delta_vs_fipe_pct": round(((ideal / fipe_value) - 1) * 100, 1) if fipe_value else 0,
            "confidence_score": confidence_score, "confidence_label": confidence_label, "comparable_count": len(matches),
            "regional_comparable_count": regional_count, "region_used": normalize_state(vehicle.state), "price_statistics": stats,
            "minimum_comparable_score": self.comparables.min_score,
            "methodology_note": "Valuation v3 usa FIPE real como âncora secundária, comparáveis reais ponderados por similaridade, mediana ponderada, percentis, média aparada, remoção de outliers, ajuste regional, km, liquidez e qualidade da amostra.",
            "low_confidence_message": "Amostra real pequena ou dispersa; preço calculado com maior peso conservador." if confidence_score < 52 else "",
            "sources": sorted({m.listing.source for m in matches}), "analysis_date": datetime.now(timezone.utc).isoformat(),
            "comparables": [self.serialize(m) for m in matches[:12]],
            "chart": [{"label":"FIPE real" if fipe_value else "FIPE indisponível", "value": round_money(fipe_value or ideal)}, {"label":"Venda rápida", "value": quick}, {"label":"Preço justo", "value": ideal}, {"label":"Valor valorizado", "value": recommended_top}],
            "liquidity_curve": [{"month":"Agora", "score": liquidity.score}, {"month":"30 dias", "score": max(30, liquidity.score-4)}, {"month":"60 dias", "score": max(25, liquidity.score-8)}, {"month":"90 dias", "score": max(20, liquidity.score-12)}],
        }
        payload["fipe_simulated"] = payload["fipe_real"] or 0
        run = ValuationRun(tenant_id=tenant_id, app_mode="REAL", brand=normalize_brand(vehicle.brand), model=normalize_model(vehicle.model), version=vehicle.version, year=vehicle.year, mileage=vehicle.km, state=normalize_state(vehicle.state), fipe_value=fipe_value, quick_sale_price=quick, ideal_price=ideal, premium_price=recommended_top, confidence_score=confidence_score, confidence_label=confidence_label, comparable_count=len(matches), payload=payload)
        db.add(run); db.flush()
        for m in matches[:20]:
            db.add(ValuationComparable(valuation_run_id=run.id, market_listing_id=m.listing.id, similarity_score=m.similarity_score, adjustments=m.details))
        db.commit()
        return payload

    def _catalog_fipe_version(self, db: Session, vehicle: ValuationInput):
        brand = normalize_brand(vehicle.brand)
        model = normalize_model(vehicle.model)
        return (
            db.query(VehicleVersion)
            .join(VehicleModel, VehicleModel.id == VehicleVersion.model_id)
            .join(VehicleBrand, VehicleBrand.id == VehicleModel.brand_id)
            .filter(VehicleBrand.canonical_name == brand, VehicleModel.canonical_name.like(f"%{model}%"), VehicleVersion.year == vehicle.year)
            .order_by(VehicleVersion.reference_month.desc())
            .first()
        )

    def km_depreciation(self, actual: int, reference: float) -> float:
        delta = (actual - max(reference, 1)) / max(reference, 1)
        return max(.84, min(1.12, 1 - delta * .13))

    def confidence(self, count: int, avg_similarity: int, dispersion: float, has_fipe: bool, liquidity: int, regional_count: int) -> tuple[int, str]:
        score = min(34, count * 3.6) + min(22, max(0, avg_similarity - 55) * .75) + max(0, 20 - dispersion * 45) + (12 if has_fipe else 0) + min(8, regional_count * 2) + min(8, liquidity / 12)
        score = int(max(10, min(100, score)))
        return score, "Alta" if score >= 76 else "Média" if score >= 52 else "Baixa"

    def serialize(self, m):
        i = m.listing
        return {"id": i.id, "title": i.title, "price": round_money(i.price), "brand": i.brand, "model": i.model, "version": i.version, "year": i.year, "mileage": i.mileage, "city": i.city, "state": i.state, "source": i.source, "url": i.url, "similarity_score": m.similarity_score, "details": m.details, "collected_at": i.collected_at.isoformat() if hasattr(i.collected_at, "isoformat") else str(i.collected_at or "")}
