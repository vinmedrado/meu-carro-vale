from pydantic import BaseModel, Field
from typing import List

class VehicleCreate(BaseModel):
    brand: str
    model: str
    version: str = ""
    year: int = Field(ge=1980, le=2035)
    km: int = Field(ge=0)
    transmission: str
    fuel: str
    color: str
    options: str = ""
    condition: str = "bom"
    city: str
    state: str
    history: str = ""
    revisions: str = ""
    notes: str = ""
    photos: List[str] = []

class VehicleOut(VehicleCreate):
    id: int

    class Config:
        from_attributes = True


class AutoValuationRequest(BaseModel):
    query: str = Field(min_length=2)
    mileage: int = Field(ge=0)
    state: str
    city: str
    condition: str = "bom"
    brand: str | None = None
    model: str | None = None
    version: str | None = None
    year: int | None = Field(default=None, ge=1980, le=2035)
    transmission: str = "Automático"
    fuel: str = "Flex"
    color: str = "Não informado"
    options: str = ""
    history: str = ""
    revisions: str = ""
