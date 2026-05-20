from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.saas import ValuationReport
from app.services.saas_service import assert_usage_available, record_usage, get_subscription_plan, monthly_usage_count
from app.schemas.vehicle import VehicleCreate, VehicleOut, AutoValuationRequest
from app.services.valuation_engine import ValuationEngine, ValuationInput
from app.services.valuation_real_engine import RealValuationEngine
from app.services.ai_insights import build_insights, build_ads
from app.intelligence.engine import MCVIntelligenceEngine
from app.data_engine_bridge import DataEngineExportLoader, DataEngineValuationAdapter
from app.vehicle_catalog.services.catalog_service import VehicleCatalogService
from app.services.data_engine_client import MCVDataEngineClient

router = APIRouter(prefix="/vehicles", tags=["vehicles"])


def _valuation_input(vehicle: dict) -> ValuationInput:
    return ValuationInput(**{k: vehicle[k] for k in ValuationInput.__annotations__.keys()})


@router.post("", response_model=VehicleOut)
def create_vehicle(data: VehicleCreate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    v = Vehicle(**data.model_dump(exclude={"photos"}), photos={"items": data.photos}, owner_id=user.id, tenant_id=user.tenant_id)
    db.add(v); db.commit(); db.refresh(v)
    return {**data.model_dump(), "id": v.id}


@router.get("")
def list_vehicles(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.query(Vehicle).filter(Vehicle.tenant_id == user.tenant_id).order_by(Vehicle.id.desc()).all()
    return [{"id": r.id, "brand": r.brand, "model": r.model, "year": r.year, "km": r.km, "city": r.city, "state": r.state} for r in rows]



def _apply_data_engine_context(vehicle: dict, valuation: dict, data_engine_payload: dict) -> dict:
    valuation["data_engine_context"] = data_engine_payload
    comparables_payload = data_engine_payload.get("comparables") or {}
    behavior_payload = data_engine_payload.get("behavior") or {}
    liquidity_payload = data_engine_payload.get("liquidity") or {}
    snapshots_payload = data_engine_payload.get("snapshots") or {}

    comps = comparables_payload.get("comparables") if isinstance(comparables_payload, dict) else []
    stats = comparables_payload.get("sample_statistics") if isinstance(comparables_payload, dict) else {}
    if comps:
        valuation["comparables"] = comps
        valuation["comparables_used"] = len(comps)
        valuation["comparable_count"] = len(comps)
        valuation["data_engine_exports_used"] = True
        valuation["data_engine_source"] = {"used": True, "mode": data_engine_payload.get("mode"), "reason": "Comparáveis oficiais do mcv-data-engine aplicados."}
        if stats:
            med = stats.get("preco_mediano") or stats.get("median_price") or stats.get("preco_p50")
            if med:
                valuation["market_reference"] = float(med)
                valuation["recommended_price"] = float(med)
                valuation["ideal_price"] = float(med)
            valuation["price_dispersion"] = stats
            valuation["confidence_label"] = stats.get("confianca_amostra") or valuation.get("confidence_label")
    else:
        valuation.setdefault("data_engine_source", {"used": False, "reason": "Amostra real indisponível; fallback seguro aplicado."})
        valuation.setdefault("low_confidence_message", "Amostra real limitada no motor de dados. O cálculo usa fallback seguro com confiança reduzida.")

    behavior = behavior_payload.get("behavior") if isinstance(behavior_payload, dict) else behavior_payload
    if isinstance(behavior, dict) and behavior:
        valuation["market_behavior"] = behavior
        valuation["executive_market_insight_v2"] = behavior.get("summary") or behavior.get("market_behavior_summary") or valuation.get("executive_market_insight_v2")
        valuation["stuck_risk_level"] = behavior.get("stuck_risk_level") or valuation.get("stuck_risk_level")
        valuation["market_temperature"] = behavior.get("trend_direction") or behavior.get("velocity_level") or valuation.get("market_temperature")
        if behavior.get("resistance_price"):
            valuation["resistance_price"] = behavior.get("resistance_price")

    liquidity = liquidity_payload.get("liquidity") if isinstance(liquidity_payload, dict) else liquidity_payload
    if isinstance(liquidity, dict):
        valuation["liquidity_from_data_engine"] = liquidity
    elif isinstance(liquidity, list) and liquidity:
        valuation["liquidity_from_data_engine"] = liquidity[:5]

    snapshots = snapshots_payload.get("snapshots") if isinstance(snapshots_payload, dict) else snapshots_payload
    if snapshots:
        valuation["snapshots_from_data_engine"] = snapshots[:10] if isinstance(snapshots, list) else snapshots

    valuation["methodology_note"] = (valuation.get("methodology_note") or "") + " Dados do mcv-data-engine foram consultados para comparáveis, liquidez, comportamento e snapshots quando disponíveis."
    return valuation


def _build_vehicle_from_auto_request(request: AutoValuationRequest, resolved: dict | None) -> VehicleCreate:
    resolved = resolved or {}
    return VehicleCreate(
        brand=str(resolved.get("brand") or request.brand or ""),
        model=str(resolved.get("model") or request.model or request.query),
        version=str(resolved.get("version") or request.version or ""),
        year=int(resolved.get("year") or request.year or 2020),
        km=int(request.mileage),
        transmission=request.transmission or "Automático",
        fuel=str(resolved.get("fuel") or request.fuel or "Flex"),
        color=request.color or "Não informado",
        options=request.options or "",
        condition=request.condition or "bom",
        city=request.city,
        state=request.state,
        history=request.history or "",
        revisions=request.revisions or "",
        notes=f"Busca original: {request.query}",
        photos=[],
    )


def _run_valuation(data: VehicleCreate, db: Session, user: User, original_query: str | None = None, resolved_vehicle: dict | None = None):
    usage_state = assert_usage_available(db, user.tenant_id)
    vehicle = data.model_dump()
    if original_query:
        vehicle["query_original"] = original_query
    if resolved_vehicle:
        vehicle["veiculo_resolvido"] = resolved_vehicle
        vehicle["fipe_code"] = resolved_vehicle.get("fipe_code")

    catalog = VehicleCatalogService()
    combined_text = " ".join([str(vehicle.get("brand", "")), str(vehicle.get("model", "")), str(vehicle.get("version", ""))])
    match = catalog.normalize_vehicle_text(db, combined_text, brand_hint=vehicle.get("brand", ""))
    if match.canonical_brand:
        vehicle["brand"] = match.canonical_brand
    if match.canonical_model:
        vehicle["model"] = match.canonical_model
    if match.version_hint and not vehicle.get("version"):
        vehicle["version"] = match.version_hint
    vehicle["catalog_match"] = match.__dict__

    client = MCVDataEngineClient()
    data_engine_payload = {
        "mode": client.mode,
        "manifest": client.load_manifest(),
        "comparables": client.get_comparables(vehicle),
        "liquidity": client.get_liquidity(vehicle),
        "behavior": client.get_behavior(vehicle),
        "snapshots": client.get_snapshots(vehicle),
    }

    app_mode = settings.app_mode.upper().strip()
    valuation_input = _valuation_input(vehicle)
    try:
        valuation = None
        if settings.use_data_engine_exports:
            valuation = DataEngineValuationAdapter(DataEngineExportLoader(settings.data_engine_exports_path)).evaluate(valuation_input)

        if valuation is None:
            if app_mode == "REAL":
                valuation = RealValuationEngine(min_comparable_score=settings.min_comparable_score).evaluate(db, valuation_input, tenant_id=user.tenant_id)
            else:
                valuation = ValuationEngine().evaluate(valuation_input)
                valuation.update({
                    "mode": "DEMO",
                    "data_badge": "Modo demonstração",
                    "confidence_score": 88,
                    "confidence_label": "Demo",
                    "comparable_count": 0,
                    "comparables": [],
                    "sources": ["dados demonstrativos para apresentação"],
                    "methodology_note": "Modo demo com fallback seguro. Configure o mcv-data-engine para usar dados reais oficiais.",
                    "fipe_real": None,
                    "fipe_source": "referência demo",
                    "data_engine_source": {"used": False, "reason": "exports indisponíveis ou sem amostra compatível"},
                })
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    valuation = _apply_data_engine_context(vehicle, valuation, data_engine_payload)
    if not valuation.get("data_engine_exports_used"):
        valuation = MCVIntelligenceEngine().enrich(db, valuation_input, valuation)

    insights = build_insights(vehicle, valuation)
    ads = build_ads(vehicle, valuation)
    image_quality = [
        {"name": p, "quality_score": 82 if i % 2 == 0 else 68, "suggestion": "Boa foto" if i % 2 == 0 else "Melhorar iluminação e enquadramento"}
        for i, p in enumerate(vehicle.get("photos", []))
    ]
    saved_vehicle = Vehicle(**data.model_dump(exclude={"photos"}), photos={"items": data.photos}, owner_id=user.id, tenant_id=user.tenant_id)
    db.add(saved_vehicle); db.commit(); db.refresh(saved_vehicle)
    recommended_value = float(valuation.get("recommended_price") or valuation.get("recommended_value") or valuation.get("preco_recomendado") or valuation.get("market_value") or valuation.get("ideal_price") or 0)
    liquidity_level = str(valuation.get("liquidity_level") or valuation.get("liquidez") or valuation.get("market_temperature") or valuation.get("stuck_risk_level") or "Não informado")
    confidence_label = str(valuation.get("confidence_label") or valuation.get("confidence_level") or valuation.get("confianca") or "Não informado")
    payload = {"vehicle": vehicle, "valuation": valuation, "insights": insights, "ads": ads, "image_quality": image_quality}
    report = ValuationReport(
        tenant_id=user.tenant_id,
        user_id=user.id,
        vehicle_id=saved_vehicle.id,
        title=f"Laudo Meu Carro Vale - {vehicle.get('brand', '')} {vehicle.get('model', '')}".strip(),
        recommended_value=recommended_value,
        liquidity_level=liquidity_level,
        confidence_label=confidence_label,
        payload=payload,
    )
    db.add(report); db.commit(); db.refresh(report)
    record_usage(db, user.tenant_id, user.id, {"report_id": report.id, "vehicle_id": saved_vehicle.id, "usage_before": usage_state, "query_original": original_query})
    _sub, plan = get_subscription_plan(db, user.tenant_id)
    used_after = monthly_usage_count(db, user.tenant_id)
    payload["saas"] = {"report_id": report.id, "vehicle_id": saved_vehicle.id, "usage": {"plan_id": plan.id, "plan_name": plan.name, "used": used_after, "limit": plan.monthly_report_limit, "remaining": max(plan.monthly_report_limit - used_after, 0)}}
    return payload


@router.post("/valuate")
def valuate(data: VehicleCreate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    return _run_valuation(data, db, user)


@router.post("/auto-valuate")
def auto_valuate(request: AutoValuationRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    client = MCVDataEngineClient()
    resolved = client.resolve_vehicle(request.query)
    if not resolved and client.mode == "api":
        raise HTTPException(status_code=503, detail="Motor de dados indisponível no momento ou sem correspondência para o veículo informado.")
    data = _build_vehicle_from_auto_request(request, resolved)
    payload = _run_valuation(data, db, user, original_query=request.query, resolved_vehicle=resolved)
    payload["busca"] = {"query": request.query, "veiculo_resolvido": resolved, "fonte": "mcv-data-engine" if resolved else "fallback seguro"}
    return payload
