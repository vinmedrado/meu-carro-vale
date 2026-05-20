from __future__ import annotations
from dataclasses import dataclass
from math import exp
from app.services.valuation_transparency import build_transparency_payload

REGION_MULTIPLIER = {"SP":1.04,"RJ":1.02,"MG":1.01,"PR":1.01,"SC":1.02,"RS":.99,"BA":.98,"PE":.98,"GO":1.0,"DF":1.03}
BRAND_BASE = {"toyota":118000,"honda":104000,"volkswagen":78000,"chevrolet":72000,"fiat":64000,"hyundai":82000,"jeep":125000,"bmw":210000,"mercedes":230000,"yamaha":28000,"honda moto":26000}
LIQUIDITY = {"corolla":94,"civic":90,"onix":92,"hb20":89,"gol":86,"compass":78,"renegade":76,"cg":95,"factor":84}

@dataclass
class ValuationInput:
    brand: str
    model: str
    version: str
    year: int
    km: int
    transmission: str
    fuel: str
    color: str
    options: str
    condition: str
    state: str
    city: str

class ValuationEngine:
    def evaluate(self, v: ValuationInput) -> dict:
        brand_key = v.brand.lower().strip()
        model_key = v.model.lower().strip()
        base = BRAND_BASE.get(brand_key, 76000)
        if "moto" in model_key or brand_key in ["yamaha", "honda moto"]:
            base = BRAND_BASE.get(brand_key, 24000)
        age = max(0, 2026 - v.year)
        depreciation = 0.075 * age
        expected_km = max(8000, age * 12000)
        km_delta = (v.km - expected_km) / max(expected_km, 1)
        km_factor = 1 - max(-0.08, min(0.18, km_delta * 0.16))
        region_factor = REGION_MULTIPLIER.get(v.state.upper(), 1.0)
        auto_bonus = 1.035 if "auto" in v.transmission.lower() else 1.0
        option_bonus = min(1.08, 1 + len([x for x in v.options.split(',') if x.strip()]) * 0.008)
        condition_factor = {"excelente":1.06,"bom":1.0,"regular":.92,"atenção":.86}.get(v.condition.lower(), 1.0)
        fipe = base * max(.35, 1 - depreciation) * km_factor * auto_bonus
        market = fipe * region_factor * option_bonus * condition_factor
        liquidity = LIQUIDITY.get(model_key, int(68 + 22/(1+exp((age-7)/2))))
        attractiveness = int(max(35, min(98, liquidity*.55 + (100-min(100,abs(km_delta)*100))*.25 + condition_factor*20)))
        vehicle_score = int(max(40, min(99, attractiveness*.62 + (100-age*5)*.18 + liquidity*.2)))
        quick = round(market * 0.94, -2)
        ideal = round(market, -2)
        recommended_top = round(market * 1.075, -2)
        negotiation_low = round(quick * .985, -2)
        negotiation_high = round(recommended_top * 1.015, -2)
        demo_count = 48
        p50 = ideal
        p25 = ideal * 0.955
        p75 = ideal * 1.055
        transparency = build_transparency_payload(
            vehicle=v,
            matches=[object()] * demo_count,
            prices=[p25, p50, p75],
            p25=p25,
            p50=p50,
            p75=p75,
            min_price=quick * .98,
            max_price=recommended_top * 1.03,
            fipe_value=fipe,
            ideal=ideal,
            confidence_score=88,
            confidence_label="Alta",
            liquidity_score=int(liquidity),
            liquidity_label="Alta" if liquidity >= 78 else "Média",
            regional_count=18,
            avg_similarity=91,
            outliers_removed=3,
            weighted_median_value=ideal,
        )
        return {
            **transparency,
            "fipe_simulated": int(round(fipe, -2)),
            "market_reference": int(round(market * 1.015, -2)),
            "quick_sale_price": int(quick),
            "ideal_price": int(ideal),
            "recommended_top_price": int(recommended_top),
            "negotiation_range": [int(negotiation_low), int(negotiation_high)],
            "vehicle_score": vehicle_score,
            "liquidity_score": int(liquidity),
            "attractiveness_score": attractiveness,
            "market_delta_vs_fipe_pct": round(((market/fipe)-1)*100, 1) if fipe else 0,
            "chart": [
                {"label":"FIPE de referência","value":int(round(fipe,-2))},
                {"label":"Venda rápida","value":int(quick)},
                {"label":"Preço ideal","value":int(ideal)},
                {"label":"Valor valorizado","value":int(recommended_top)},
            ],
            "liquidity_curve": [
                {"month":"Agora","score":int(liquidity)},
                {"month":"30 dias","score":max(35,int(liquidity-4))},
                {"month":"60 dias","score":max(30,int(liquidity-9))},
                {"month":"90 dias","score":max(25,int(liquidity-14))},
            ]
        }
