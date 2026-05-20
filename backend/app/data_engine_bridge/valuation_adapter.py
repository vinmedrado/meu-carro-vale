from __future__ import annotations

import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.data_engine_bridge.loader import DataEngineExportLoader
from app.services.valuation_engine import ValuationInput
from app.services.valuation_transparency import build_transparency_payload
from app.intelligence.sales.selling_decision_engine import SellingDecisionEngine

try:
    import pandas as pd
except Exception:  # pragma: no cover
    pd = None  # type: ignore


def _norm(value: Any) -> str:
    text = str(value or "").strip().lower()
    for a, b in [("á", "a"), ("à", "a"), ("ã", "a"), ("â", "a"), ("é", "e"), ("ê", "e"), ("í", "i"), ("ó", "o"), ("õ", "o"), ("ô", "o"), ("ú", "u"), ("ç", "c")]:
        text = text.replace(a, b)
    return " ".join(text.replace("-", " ").replace("_", " ").split())


def _money(value: float | int | None) -> int:
    return int(round(float(value or 0) / 100) * 100)


def _quantile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = (len(ordered) - 1) * q
    lo = int(idx)
    hi = min(lo + 1, len(ordered) - 1)
    w = idx - lo
    return ordered[lo] * (1 - w) + ordered[hi] * w


class DataEngineValuationAdapter:
    """Transforma exports oficiais do mcv-data-engine em valuation do Meu Carro Vale.

    Regras:
    - usa comparables/snapshots/liquidity/market_behavior quando existem e passam no contrato;
    - não coleta nem faz scraping;
    - devolve None quando não há dado real suficiente, permitindo fallback seguro.
    """

    def __init__(self, loader: DataEngineExportLoader | None = None):
        self.loader = loader or DataEngineExportLoader()
        self.selling_decision = SellingDecisionEngine()

    def evaluate(self, vehicle: ValuationInput) -> dict[str, Any] | None:
        validation = self.loader.validate_exports()
        if not validation.available:
            return None
        comps = self._filter_comparables(vehicle)
        snapshots = self._filter_snapshots(vehicle)
        if comps.empty and snapshots.empty:
            return None
        liquidity = self._filter_liquidity(vehicle)
        behavior = self._filter_behavior(vehicle)
        prices = self._prices_from(comps, snapshots)
        if not prices:
            return None
        p25 = _quantile(prices, .25)
        p50 = _quantile(prices, .50)
        p75 = _quantile(prices, .75)
        snapshot_row = snapshots.iloc[0].to_dict() if not snapshots.empty else {}
        if snapshot_row:
            p25 = float(snapshot_row.get("preco_p25") or p25)
            p50 = float(snapshot_row.get("preco_mediano") or p50)
            p75 = float(snapshot_row.get("preco_p75") or p75)
        dispersion = ((p75 - p25) / p50) if p50 else 0.0
        ideal = _money(p50)
        quick = _money(ideal * .94)
        recommended_top = _money(max(p75, ideal * 1.07))
        negotiation_floor = _money(max(quick * .985, p25 * .985))
        negotiation_ceiling = _money(recommended_top * 1.015)
        comparable_count = int(len(comps)) if not comps.empty else int(snapshot_row.get("qtd_anuncios") or len(prices))
        regional_count = int(len(comps[comps.get("regional_match", False).astype(bool)])) if not comps.empty and "regional_match" in comps else comparable_count
        avg_similarity = int(round(float(comps["comparable_score"].mean()))) if not comps.empty and "comparable_score" in comps else 72
        liquidity_payload = self._liquidity_payload(liquidity, behavior, comparable_count, dispersion)
        confidence_score, confidence_label = self._confidence(comparable_count, avg_similarity, dispersion, validation.manifest.get("quality_score", 0.75))
        transparency = build_transparency_payload(
            vehicle=vehicle,
            matches=[object()] * comparable_count,
            prices=prices,
            p25=p25,
            p50=p50,
            p75=p75,
            min_price=min(prices),
            max_price=max(prices),
            fipe_value=None,
            ideal=ideal,
            confidence_score=confidence_score,
            confidence_label=confidence_label,
            liquidity_score=liquidity_payload["liquidity_score"],
            liquidity_label=liquidity_payload["liquidity_label"],
            regional_count=regional_count,
            avg_similarity=avg_similarity,
            outliers_removed=0,
            weighted_median_value=p50,
            market_weight=1.0,
            fipe_weight=0.0,
        )
        comparables_payload = self._serialize_comparables(comps)
        behavior_payload = behavior.iloc[0].to_dict() if not behavior.empty else {}
        selling_decision = self.selling_decision.analyze(
            valuation={"ideal_price": ideal, "quick_sale_price": quick, "confidence_score": confidence_score},
            negotiation={"recommended_price": ideal, "quick_sale_price": quick, "negotiation_floor": negotiation_floor, "negotiation_ceiling": negotiation_ceiling},
            liquidity={"demand_index": liquidity_payload["demand_index"], "pressure_score": liquidity_payload["pressure_score"]},
            confidence={"confidence_score": confidence_score},
            comparables={"comparables_used": comparable_count, "price_dispersion_index": round(dispersion, 4), "comparables": comparables_payload},
            positioning={"market_position_percentile": self._position_percentile(ideal, prices)},
            buyer_behavior={"km_sensitivity": "média"},
        )
        explanation = self._explanation(vehicle, ideal, p50, dispersion, liquidity_payload, behavior_payload, comps)
        payload: dict[str, Any] = {
            **transparency,
            "mode": "DATA_ENGINE_EXPORTS",
            "data_badge": "Dados reais do mcv-data-engine",
            "data_engine_exports_used": True,
            "data_engine_source": {
                "used": True,
                "exports_path": str(self.loader.exports_path),
                "manifest_generated_at": validation.manifest.get("generated_at"),
                "schema_registry_version": validation.manifest.get("schema_registry_version"),
                "validation_status": validation.status,
                "quality_score": validation.manifest.get("quality_score"),
            },
            "market_reference": ideal,
            "quick_sale_price": quick,
            "ideal_price": ideal,
            "recommended_top_price": recommended_top,
            "negotiation_range": [negotiation_floor, negotiation_ceiling],
            "recommended_price": ideal,
            "negotiation_floor": negotiation_floor,
            "negotiation_ceiling": negotiation_ceiling,
            "fipe_real": None,
            "fipe_simulated": 0,
            "fipe_source": "FIPE disponível no data engine/catálogo quando exportada; valuation atual priorizou comparáveis reais oficiais.",
            "comparable_count": comparable_count,
            "comparables": comparables_payload,
            "sources": sorted({str(x) for x in comps.get("fonte", [])}) if not comps.empty and "fonte" in comps else ["mcv-data-engine"],
            "price_statistics": {
                "p25": _money(p25), "p50": _money(p50), "p75": _money(p75), "weighted_median": _money(p50),
                "count_after_outlier_filter": comparable_count, "dispersion": round(dispersion, 4), "outliers_removed": 0,
            },
            "confidence_score": confidence_score,
            "confidence_label": confidence_label,
            "confidence_level": confidence_label,
            "confidence_reason": f"Contrato validado pelo mcv-data-engine, {comparable_count} comparáveis/snapshots úteis e similaridade média de {avg_similarity}/100.",
            "analysis_quality": "alta" if confidence_score >= 78 else "boa" if confidence_score >= 62 else "conservadora",
            "liquidity_score": liquidity_payload["liquidity_score"],
            "liquidity_label": liquidity_payload["liquidity_label"],
            "liquidity_level": liquidity_payload["liquidity_label"],
            "market_temperature": liquidity_payload["market_temperature"],
            "market_temperature_label": liquidity_payload["market_temperature"],
            "sale_velocity": liquidity_payload["sale_velocity"],
            "demand_index": liquidity_payload["demand_index"],
            "pressure_score": liquidity_payload["pressure_score"],
            "trend_direction": str(behavior_payload.get("trend_direction") or snapshot_row.get("temperatura_mercado") or "Estável"),
            "regional_market_temperature": str(behavior_payload.get("regional_strength") or snapshot_row.get("temperatura_mercado") or "Em observação"),
            "stuck_risk_level": str(behavior_payload.get("stuck_risk_level") or selling_decision.get("stuck_risk_level") or "Moderado"),
            "resistance_price": _money(float(behavior_payload.get("resistance_price") or negotiation_ceiling)),
            "executive_market_insight": str(behavior_payload.get("summary") or explanation["executive_summary"]),
            "executive_market_insight_v2": str(behavior_payload.get("summary") or explanation["executive_summary"]),
            "valuation_explanation": explanation["factors"],
            "valuation_explanation_text": explanation["text"],
            "comparable_analysis": explanation["comparable_analysis"],
            "regional_explanation": explanation["regional_explanation"],
            "market_temperature_detail": explanation["market_temperature_detail"],
            "selling_decision": selling_decision,
            "listing_price": selling_decision["listing_price"],
            "ideal_close_range_min": selling_decision["ideal_close_range_min"],
            "ideal_close_range_max": selling_decision["ideal_close_range_max"],
            "minimum_recommended_price": selling_decision["minimum_recommended_price"],
            "review_price_after_days": selling_decision["review_price_after_days"],
            "suggested_price_cut_percent": selling_decision["suggested_price_cut_percent"],
            "negotiation_signal": selling_decision["negotiation_signal"],
            "negotiation_message": selling_decision["negotiation_message"],
            "price_defense_arguments": selling_decision["price_defense_arguments"],
            "seller_summary": selling_decision["seller_summary"],
            "methodology_note": "Valuation calculado a partir dos exports oficiais do mcv-data-engine: comparáveis limpos, snapshots, liquidez, comportamento de mercado, contrato validado e fallback seguro quando não houver dado suficiente.",
            "chart": [
                {"label": "Faixa inferior", "value": _money(p25)},
                {"label": "Venda rápida", "value": quick},
                {"label": "Valor de mercado", "value": ideal},
                {"label": "Teto de negociação", "value": negotiation_ceiling},
            ],
            "liquidity_curve": [
                {"month": "Agora", "score": liquidity_payload["liquidity_score"]},
                {"month": "30 dias", "score": max(25, liquidity_payload["liquidity_score"] - 4)},
                {"month": "60 dias", "score": max(20, liquidity_payload["liquidity_score"] - 8)},
                {"month": "90 dias", "score": max(15, liquidity_payload["liquidity_score"] - 12)},
            ],
            "analysis_date": datetime.now(timezone.utc).isoformat(),
        }
        return payload

    def _filter_comparables(self, vehicle: ValuationInput):
        df = self.loader.safe_read_export("comparables")
        if pd is None or getattr(df, "empty", True):
            return pd.DataFrame() if pd is not None else []
        brand = _norm(vehicle.brand); model = _norm(vehicle.model); state = str(vehicle.state or "").upper()
        mask = df["marca"].map(_norm).eq(brand) & df["modelo"].map(_norm).eq(model) & (df["ano"].astype(int).sub(int(vehicle.year)).abs() <= 1)
        if state and "estado" in df.columns:
            regional = mask & df["estado"].astype(str).str.upper().eq(state)
            if regional.sum() >= 2:
                mask = regional
        result = df[mask].copy()
        if "comparable_score" in result.columns:
            result = result.sort_values(["comparable_score", "price_delta"], ascending=[False, True], key=lambda s: s.abs() if s.name == "price_delta" else s)
        return result.head(24)

    def _filter_snapshots(self, vehicle: ValuationInput):
        df = self.loader.safe_read_export("snapshots")
        if pd is None or getattr(df, "empty", True):
            return pd.DataFrame() if pd is not None else []
        brand = _norm(vehicle.brand); model = _norm(vehicle.model); state = str(vehicle.state or "").upper()
        mask = df["marca"].map(_norm).eq(brand) & df["modelo"].map(_norm).eq(model) & df["ano"].astype(int).eq(int(vehicle.year))
        if state and "estado" in df.columns:
            regional = mask & df["estado"].astype(str).str.upper().eq(state)
            if regional.any(): mask = regional
        return df[mask].copy().head(3)

    def _filter_liquidity(self, vehicle: ValuationInput):
        df = self.loader.safe_read_export("liquidity")
        if pd is None or getattr(df, "empty", True):
            return pd.DataFrame() if pd is not None else []
        brand = _norm(vehicle.brand); model = _norm(vehicle.model); state = str(vehicle.state or "").upper()
        mask = df["marca"].map(_norm).eq(brand) & df["modelo"].map(_norm).eq(model) & df["ano"].astype(int).eq(int(vehicle.year))
        if state and "regiao" in df.columns:
            regional = mask & df["regiao"].astype(str).str.upper().eq(state)
            if regional.any(): mask = regional
        return df[mask].copy().head(1)

    def _filter_behavior(self, vehicle: ValuationInput):
        df = self.loader.safe_read_export("market_behavior")
        if pd is None or getattr(df, "empty", True):
            return pd.DataFrame() if pd is not None else []
        brand = _norm(vehicle.brand); model = _norm(vehicle.model); state = str(vehicle.state or "").upper()
        mask = df["brand"].map(_norm).eq(brand) & df["model"].map(_norm).eq(model) & df["year"].astype(int).eq(int(vehicle.year))
        if state and "state" in df.columns:
            regional = mask & df["state"].astype(str).str.upper().eq(state)
            if regional.any(): mask = regional
        return df[mask].copy().head(1)

    def _prices_from(self, comps: Any, snapshots: Any) -> list[float]:
        prices: list[float] = []
        if pd is not None and not getattr(comps, "empty", True) and "preco_comparavel" in comps:
            prices.extend([float(x) for x in comps["preco_comparavel"].dropna().tolist() if float(x) > 5000])
        if not prices and pd is not None and not getattr(snapshots, "empty", True):
            row = snapshots.iloc[0]
            prices.extend([float(row.get(col)) for col in ["preco_p25", "preco_mediano", "preco_p75"] if row.get(col) and float(row.get(col)) > 5000])
        return prices

    def _serialize_comparables(self, comps: Any) -> list[dict[str, Any]]:
        if pd is None or getattr(comps, "empty", True):
            return []
        items: list[dict[str, Any]] = []
        for idx, row in comps.head(12).iterrows():
            items.append({
                "id": str(row.get("comparable_id") or idx),
                "title": f"{row.get('marca', '')} {row.get('modelo', '')} {row.get('versao', '')}".strip(),
                "price": _money(row.get("preco_comparavel")),
                "year": int(row.get("ano") or 0),
                "mileage": int(row.get("km_comparavel") or 0),
                "city": str(row.get("cidade") or ""),
                "state": str(row.get("estado") or ""),
                "source": str(row.get("fonte") or "mcv-data-engine"),
                "url": str(row.get("url") or ""),
                "similarity_score": round(float(row.get("comparable_score") or row.get("score") or 0), 1),
                "match_quality": str(row.get("match_quality") or ""),
                "price_delta": _money(row.get("price_delta")),
                "km_delta": int(row.get("km_delta") or 0),
                "year_delta": int(row.get("year_delta") or 0),
                "regional_match": bool(row.get("regional_match")),
                "explanation": str(row.get("explanation") or "Comparável selecionado pelo mcv-data-engine."),
                "price_impact": str(row.get("price_impact") or "neutro"),
            })
        return items

    def _liquidity_payload(self, liquidity: Any, behavior: Any, count: int, dispersion: float) -> dict[str, Any]:
        row = liquidity.iloc[0].to_dict() if pd is not None and not getattr(liquidity, "empty", True) else {}
        beh = behavior.iloc[0].to_dict() if pd is not None and not getattr(behavior, "empty", True) else {}
        level = str(row.get("liquidity_level") or ("Alta" if count >= 8 and dispersion <= .18 else "Média" if count >= 4 else "Baixa"))
        base = 82 if level in {"Muito Alta", "Alta"} else 62 if level == "Média" else 44
        if count >= 10: base += 6
        if dispersion <= .12: base += 5
        if dispersion >= .28: base -= 10
        pressure_raw = float(row.get("pressao_mercado") or 0) * 100 if row else 0
        return {
            "liquidity_score": max(20, min(95, int(base))),
            "liquidity_label": level,
            "market_temperature": str(row.get("temperatura_mercado") or beh.get("pressure_level") or "Em observação"),
            "sale_velocity": str(row.get("velocidade_venda_estimada") or beh.get("velocity_level") or "em análise"),
            "demand_index": max(20, min(95, int(base - min(22, pressure_raw)))) if pressure_raw else max(20, min(95, int(base))),
            "pressure_score": max(0, min(100, int(pressure_raw or (dispersion * 220))))
        }

    def _confidence(self, count: int, avg_similarity: int, dispersion: float, manifest_quality: float) -> tuple[int, str]:
        score = int(min(95, max(35, count * 4 + avg_similarity * .45 + float(manifest_quality or .75) * 18 - dispersion * 50)))
        label = "Alta" if score >= 76 else "Média" if score >= 58 else "Baixa"
        return score, label

    def _position_percentile(self, ideal: int, prices: list[float]) -> int:
        if not prices:
            return 50
        below = len([p for p in prices if p <= ideal])
        return max(1, min(99, int(round(below / len(prices) * 100))))

    def _explanation(self, vehicle: ValuationInput, ideal: int, median_price: float, dispersion: float, liquidity: dict[str, Any], behavior: dict[str, Any], comps: Any) -> dict[str, Any]:
        factors: list[dict[str, Any]] = []
        demand = int(liquidity.get("demand_index") or 50)
        if demand >= 70:
            factors.append({"factor": "Liquidez regional", "impact_value": _money(ideal * .018), "impact_direction": "positivo", "weight": 16, "reason": "demanda e volume sustentam venda com menor desconto"})
        elif demand < 50:
            factors.append({"factor": "Liquidez regional", "impact_value": -_money(ideal * .016), "impact_direction": "negativo", "weight": 16, "reason": "mercado exige preço mais defensivo"})
        if dispersion <= .14:
            factors.append({"factor": "Dispersão de preços", "impact_value": _money(ideal * .009), "impact_direction": "positivo", "weight": 12, "reason": "comparáveis concentrados indicam referência mais estável"})
        elif dispersion >= .25:
            factors.append({"factor": "Dispersão de preços", "impact_value": -_money(ideal * .014), "impact_direction": "negativo", "weight": 12, "reason": "preços muito espalhados aumentam cautela na faixa"})
        if pd is not None and not getattr(comps, "empty", True) and "km_delta" in comps:
            avg_km_delta = float(comps["km_delta"].mean())
            if avg_km_delta > 5000:
                factors.append({"factor": "Quilometragem", "impact_value": _money(ideal * .011), "impact_direction": "positivo", "weight": 10, "reason": "comparáveis próximos possuem quilometragem média maior"})
            elif avg_km_delta < -5000:
                factors.append({"factor": "Quilometragem", "impact_value": -_money(ideal * .01), "impact_direction": "negativo", "weight": 10, "reason": "comparáveis próximos possuem quilometragem média menor"})
        pressure = str(behavior.get("pressure_level") or "")
        if "alta" in pressure.lower() or "pressionado" in pressure.lower():
            factors.append({"factor": "Pressão de mercado", "impact_value": -_money(ideal * .017), "impact_direction": "negativo", "weight": 11, "reason": "oferta concorrente pode limitar preço no topo da faixa"})
        comparable_analysis = self._serialize_comparables(comps)[:8] if pd is not None else []
        text = "Valor definido por comparáveis oficiais, snapshot de preço e comportamento de mercado do mcv-data-engine."
        if factors:
            parts = []
            for f in factors[:4]:
                signal = "+" if f["impact_direction"] == "positivo" else "-"
                parts.append(f"{signal}R$ {abs(int(f['impact_value'])):,.0f}".replace(",", ".") + f" por {f['reason']}")
            text = "; ".join(parts) + "."
        return {
            "factors": factors,
            "text": text,
            "comparable_analysis": comparable_analysis,
            "regional_explanation": f"A leitura priorizou {vehicle.city}/{vehicle.state} quando havia amostra regional; caso contrário, usou o recorte estadual dos exports oficiais.",
            "market_temperature_detail": str(behavior.get("summary") or f"Temperatura: {liquidity.get('market_temperature')} com liquidez {liquidity.get('liquidity_label')}"),
            "executive_summary": f"O veículo foi avaliado com base em {len(comparable_analysis) or 'amostra de'} comparáveis oficiais e comportamento de mercado validado. A faixa recomendada favorece negociação próxima de R$ {ideal:,.0f}.".replace(",", "."),
        }
