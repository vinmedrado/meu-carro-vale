from pydantic import BaseModel, Field
from typing import Any


class MarketListingOut(BaseModel):
    title: str
    price: float = Field(ge=0)
    brand: str
    model: str
    version: str = ""
    year: int
    mileage: int
    city: str = ""
    state: str = ""
    transmission: str = ""
    fuel: str = ""
    url: str = ""
    source: str = "csv"
    collected_at: str | None = None


class ImportSummary(BaseModel):
    imported: int
    ignored: int
    duplicates: int
    total_rows: int
    errors: list[str] = []
