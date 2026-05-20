from pydantic import BaseModel

class CatalogBrandOut(BaseModel):
    id: int
    vehicle_type: str
    canonical_name: str
    fipe_code: str
    is_active: bool

class CatalogModelOut(BaseModel):
    id: int
    brand_id: int
    canonical_name: str
    fipe_code: str
    is_active: bool

class CatalogVersionOut(BaseModel):
    id: int
    model_id: int
    fipe_year_code: str
    year: int
    fuel: str
    version_name: str
    fipe_code: str
    reference_month: str
    fipe_price: float
