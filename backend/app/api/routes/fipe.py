from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.fipe_service import FipeService

router = APIRouter(prefix="/fipe", tags=["fipe"])
service = FipeService()


@router.get("/brands")
def get_brands(vehicle_type: str = Query("carros", description="carros, motos ou caminhoes")):
    try:
        return service.brands(vehicle_type)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"FIPE indisponível: {exc}") from exc


@router.get("/models")
def get_models(vehicle_type: str = "carros", brand_code: str = Query(...)):
    try:
        return service.models(vehicle_type, brand_code)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"FIPE indisponível: {exc}") from exc


@router.get("/years")
def get_years(vehicle_type: str = "carros", brand_code: str = Query(...), model_code: str = Query(...)):
    try:
        return service.years(vehicle_type, brand_code, model_code)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"FIPE indisponível: {exc}") from exc


@router.get("/price")
def get_price(
    vehicle_type: str = "carros",
    brand_code: str = Query(...),
    model_code: str = Query(...),
    year_code: str = Query(...),
    db: Session = Depends(get_db),
):
    try:
        return service.price(db, vehicle_type, brand_code, model_code, year_code)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"FIPE indisponível: {exc}") from exc
