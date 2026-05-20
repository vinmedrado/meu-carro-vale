from __future__ import annotations

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db.session import Base


class VehicleBrand(Base):
    __tablename__ = "vehicle_brands"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    vehicle_type: Mapped[str] = mapped_column(String(20), index=True)
    canonical_name: Mapped[str] = mapped_column(String(100), index=True)
    fipe_code: Mapped[str] = mapped_column(String(40), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    aliases = relationship("VehicleBrandAlias", cascade="all, delete-orphan", back_populates="brand")
    models = relationship("VehicleModel", cascade="all, delete-orphan", back_populates="brand")
    __table_args__ = (UniqueConstraint("vehicle_type", "fipe_code", name="uq_vehicle_brand_type_fipe"),)


class VehicleBrandAlias(Base):
    __tablename__ = "vehicle_brand_aliases"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("vehicle_brands.id"), index=True)
    alias: Mapped[str] = mapped_column(String(120), index=True)
    source: Mapped[str] = mapped_column(String(60), default="manual")
    brand = relationship("VehicleBrand", back_populates="aliases")
    __table_args__ = (UniqueConstraint("brand_id", "alias", name="uq_vehicle_brand_alias"),)


class VehicleModel(Base):
    __tablename__ = "vehicle_models"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("vehicle_brands.id"), index=True)
    canonical_name: Mapped[str] = mapped_column(String(160), index=True)
    fipe_code: Mapped[str] = mapped_column(String(40), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    brand = relationship("VehicleBrand", back_populates="models")
    aliases = relationship("VehicleModelAlias", cascade="all, delete-orphan", back_populates="model")
    versions = relationship("VehicleVersion", cascade="all, delete-orphan", back_populates="model")
    __table_args__ = (UniqueConstraint("brand_id", "fipe_code", name="uq_vehicle_model_brand_fipe"), Index("ix_vehicle_models_brand_name", "brand_id", "canonical_name"),)


class VehicleModelAlias(Base):
    __tablename__ = "vehicle_model_aliases"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("vehicle_models.id"), index=True)
    alias: Mapped[str] = mapped_column(String(180), index=True)
    source: Mapped[str] = mapped_column(String(60), default="manual")
    model = relationship("VehicleModel", back_populates="aliases")
    __table_args__ = (UniqueConstraint("model_id", "alias", name="uq_vehicle_model_alias"),)


class VehicleVersion(Base):
    __tablename__ = "vehicle_versions"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("vehicle_models.id"), index=True)
    fipe_year_code: Mapped[str] = mapped_column(String(40), index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    fuel: Mapped[str] = mapped_column(String(50), index=True, default="")
    version_name: Mapped[str] = mapped_column(String(220), index=True, default="")
    fipe_code: Mapped[str] = mapped_column(String(40), index=True, default="")
    reference_month: Mapped[str] = mapped_column(String(80), index=True, default="")
    fipe_price: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    model = relationship("VehicleModel", back_populates="versions")
    __table_args__ = (UniqueConstraint("model_id", "fipe_year_code", "reference_month", name="uq_vehicle_version_model_year_ref"),)


class VehicleCatalogSyncLog(Base):
    __tablename__ = "vehicle_catalog_sync_logs"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    status: Mapped[str] = mapped_column(String(30), index=True)
    vehicle_type: Mapped[str] = mapped_column(String(20), index=True, default="all")
    brands_count: Mapped[int] = mapped_column(Integer, default=0)
    models_count: Mapped[int] = mapped_column(Integer, default=0)
    versions_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class VehicleCatalogSyncJob(Base):
    __tablename__ = "vehicle_catalog_sync_jobs"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    status: Mapped[str] = mapped_column(String(30), index=True, default="pending")
    vehicle_type: Mapped[str] = mapped_column(String(20), index=True, default="all")
    total_brands: Mapped[int] = mapped_column(Integer, default=0)
    processed_brands: Mapped[int] = mapped_column(Integer, default=0)
    total_models: Mapped[int] = mapped_column(Integer, default=0)
    processed_models: Mapped[int] = mapped_column(Integer, default=0)
    total_versions: Mapped[int] = mapped_column(Integer, default=0)
    processed_versions: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
