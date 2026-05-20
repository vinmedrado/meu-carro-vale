from sqlalchemy import String, Integer, Text, ForeignKey, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base

class Vehicle(Base):
    __tablename__ = "vehicles"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    brand: Mapped[str] = mapped_column(String(80))
    model: Mapped[str] = mapped_column(String(100))
    version: Mapped[str] = mapped_column(String(120), default="")
    year: Mapped[int] = mapped_column(Integer)
    km: Mapped[int] = mapped_column(Integer)
    transmission: Mapped[str] = mapped_column(String(50))
    fuel: Mapped[str] = mapped_column(String(50))
    color: Mapped[str] = mapped_column(String(50))
    options: Mapped[str] = mapped_column(Text, default="")
    condition: Mapped[str] = mapped_column(String(50), default="bom")
    city: Mapped[str] = mapped_column(String(80))
    state: Mapped[str] = mapped_column(String(2))
    history: Mapped[str] = mapped_column(Text, default="")
    revisions: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    photos: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
