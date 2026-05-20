from pydantic import BaseModel, Field


class FipeBrand(BaseModel):
    code: str
    name: str


class FipeModel(BaseModel):
    code: str
    name: str


class FipeYear(BaseModel):
    code: str
    name: str


class FipePriceOut(BaseModel):
    vehicle_type: str
    brand: str
    model: str
    year: int
    fipe_code: str
    fuel: str = ""
    reference_month: str = ""
    value: float = Field(ge=0)
