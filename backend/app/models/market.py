from sqlalchemy import DateTime, Float, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.db.session import Base


class FipePrice(Base):
    __tablename__ = "fipe_prices"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    vehicle_type: Mapped[str] = mapped_column(String(20), index=True)
    brand: Mapped[str] = mapped_column(String(90), index=True)
    model: Mapped[str] = mapped_column(String(140), index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    fipe_code: Mapped[str] = mapped_column(String(40), index=True)
    fuel: Mapped[str] = mapped_column(String(50), default="")
    reference_month: Mapped[str] = mapped_column(String(80), default="")
    value: Mapped[float] = mapped_column(Float)
    raw: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("vehicle_type", "fipe_code", "year", "fuel", name="uq_fipe_vehicle_code_year_fuel"),
    )


class MarketListing(Base):
    __tablename__ = "market_listings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(240), index=True)
    price: Mapped[float] = mapped_column(Float, index=True)
    brand: Mapped[str] = mapped_column(String(90), index=True)
    model: Mapped[str] = mapped_column(String(140), index=True)
    version: Mapped[str] = mapped_column(String(160), default="")
    year: Mapped[int] = mapped_column(Integer, index=True)
    mileage: Mapped[int] = mapped_column(Integer, index=True)
    city: Mapped[str] = mapped_column(String(90), default="")
    state: Mapped[str] = mapped_column(String(2), index=True)
    transmission: Mapped[str] = mapped_column(String(50), default="")
    fuel: Mapped[str] = mapped_column(String(50), default="")
    url: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(60), index=True)
    seller_type: Mapped[str] = mapped_column(String(40), default="")
    normalized_key: Mapped[str] = mapped_column(String(500), index=True, default="")
    fingerprint: Mapped[str] = mapped_column(String(80), index=True, default="")
    duplicate_score: Mapped[int] = mapped_column(Integer, index=True, default=0)
    is_active: Mapped[bool] = mapped_column(default=True)
    raw: Mapped[dict] = mapped_column(JSON, default=dict)
    collected_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (
        Index("ix_market_lookup", "brand", "model", "year", "state", "mileage", "source", "collected_at"),
    )


class ValuationRun(Base):
    __tablename__ = "valuation_runs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True, default="demo")
    app_mode: Mapped[str] = mapped_column(String(20), index=True)
    brand: Mapped[str] = mapped_column(String(90), index=True)
    model: Mapped[str] = mapped_column(String(140), index=True)
    version: Mapped[str] = mapped_column(String(160), default="")
    year: Mapped[int] = mapped_column(Integer, index=True)
    mileage: Mapped[int] = mapped_column(Integer)
    state: Mapped[str] = mapped_column(String(2), index=True)
    fipe_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    quick_sale_price: Mapped[float] = mapped_column(Float)
    ideal_price: Mapped[float] = mapped_column(Float)
    premium_price: Mapped[float] = mapped_column(Float)
    confidence_score: Mapped[int] = mapped_column(Integer)
    confidence_label: Mapped[str] = mapped_column(String(30))
    comparable_count: Mapped[int] = mapped_column(Integer)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class ValuationComparable(Base):
    __tablename__ = "valuation_comparables"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    valuation_run_id: Mapped[int] = mapped_column(Integer, index=True)
    market_listing_id: Mapped[int] = mapped_column(Integer, index=True)
    similarity_score: Mapped[int] = mapped_column(Integer, index=True)
    adjustments: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MarketListingHistory(Base):
    __tablename__ = "market_listing_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    market_listing_id: Mapped[int] = mapped_column(Integer, index=True)
    price: Mapped[float] = mapped_column(Float, index=True)
    mileage: Mapped[int] = mapped_column(Integer, default=0)
    source: Mapped[str] = mapped_column(String(60), index=True, default="")
    raw: Mapped[dict] = mapped_column(JSON, default=dict)
    captured_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    snapshot_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    total_listings: Mapped[int] = mapped_column(Integer, default=0)
    active_listings: Mapped[int] = mapped_column(Integer, default=0)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)


class MarketPriceStats(Base):
    __tablename__ = "market_price_stats"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    brand: Mapped[str] = mapped_column(String(90), index=True)
    model: Mapped[str] = mapped_column(String(140), index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    state: Mapped[str] = mapped_column(String(2), index=True, default="")
    listing_count: Mapped[int] = mapped_column(Integer, default=0)
    p25: Mapped[float] = mapped_column(Float, default=0)
    p50: Mapped[float] = mapped_column(Float, default=0)
    p75: Mapped[float] = mapped_column(Float, default=0)
    avg_price: Mapped[float] = mapped_column(Float, default=0)
    min_price: Mapped[float] = mapped_column(Float, default=0)
    max_price: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class MarketLiquidity(Base):
    __tablename__ = "market_liquidity"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    brand: Mapped[str] = mapped_column(String(90), index=True)
    model: Mapped[str] = mapped_column(String(140), index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    state: Mapped[str] = mapped_column(String(2), index=True, default="")
    listing_count: Mapped[int] = mapped_column(Integer, default=0)
    liquidity_score: Mapped[int] = mapped_column(Integer, default=0)
    liquidity_label: Mapped[str] = mapped_column(String(30), default="Baixa")
    dispersion: Mapped[float] = mapped_column(Float, default=0)
    regional_volume: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class MarketCollectionJob(Base):
    __tablename__ = "market_collection_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    source: Mapped[str] = mapped_column(String(60), index=True)
    status: Mapped[str] = mapped_column(String(30), index=True, default="queued")
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    imported_count: Mapped[int] = mapped_column(Integer, default=0)
    duplicate_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    started_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[str | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ComparableVehicle(Base):
    __tablename__ = "comparable_vehicles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    valuation_run_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    market_listing_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    brand: Mapped[str] = mapped_column(String(90), index=True, default="")
    model: Mapped[str] = mapped_column(String(140), index=True, default="")
    version: Mapped[str] = mapped_column(String(160), default="")
    year: Mapped[int] = mapped_column(Integer, index=True, default=0)
    mileage: Mapped[int] = mapped_column(Integer, index=True, default=0)
    state: Mapped[str] = mapped_column(String(2), index=True, default="")
    source: Mapped[str] = mapped_column(String(60), index=True, default="")
    price: Mapped[float] = mapped_column(Float, index=True, default=0)
    similarity_score: Mapped[int] = mapped_column(Integer, index=True, default=0)
    regional_similarity: Mapped[int] = mapped_column(Integer, default=0)
    km_similarity: Mapped[int] = mapped_column(Integer, default=0)
    market_distance: Mapped[float] = mapped_column(Float, default=0)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (Index("ix_comparable_lookup", "brand", "model", "year", "state", "similarity_score"),)


class ValuationConfidence(Base):
    __tablename__ = "valuation_confidence"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    valuation_run_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    confidence_score: Mapped[int] = mapped_column(Integer, index=True, default=0)
    confidence_level: Mapped[str] = mapped_column(String(30), index=True, default="Baixa")
    confidence_reason: Mapped[str] = mapped_column(Text, default="")
    analysis_quality: Mapped[str] = mapped_column(String(40), default="exploratória")
    comparable_count: Mapped[int] = mapped_column(Integer, default=0)
    dispersion: Mapped[float] = mapped_column(Float, default=0)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class NegotiationRange(Base):
    __tablename__ = "negotiation_ranges"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    valuation_run_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
    quick_sale_price: Mapped[float] = mapped_column(Float, default=0)
    recommended_price: Mapped[float] = mapped_column(Float, default=0)
    negotiation_floor: Mapped[float] = mapped_column(Float, default=0)
    negotiation_ceiling: Mapped[float] = mapped_column(Float, default=0)
    estimated_negotiation_margin: Mapped[float] = mapped_column(Float, default=0)
    positioning: Mapped[str] = mapped_column(String(40), default="equilibrado")
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class RegionalValuation(Base):
    __tablename__ = "regional_valuation"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    brand: Mapped[str] = mapped_column(String(90), index=True, default="")
    model: Mapped[str] = mapped_column(String(140), index=True, default="")
    year: Mapped[int] = mapped_column(Integer, index=True, default=0)
    state: Mapped[str] = mapped_column(String(2), index=True, default="")
    regional_multiplier: Mapped[float] = mapped_column(Float, default=1.0)
    regional_market_temperature: Mapped[str] = mapped_column(String(40), default="Equilibrado")
    regional_price_delta: Mapped[float] = mapped_column(Float, default=0)
    sample_size: Mapped[int] = mapped_column(Integer, default=0)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (Index("ix_regional_valuation_lookup", "brand", "model", "year", "state"),)


class MarketTrend(Base):
    __tablename__ = "market_trends"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    brand: Mapped[str] = mapped_column(String(90), index=True, default="")
    model: Mapped[str] = mapped_column(String(140), index=True, default="")
    year: Mapped[int] = mapped_column(Integer, index=True, default=0)
    state: Mapped[str] = mapped_column(String(2), index=True, default="")
    trend_direction: Mapped[str] = mapped_column(String(30), index=True, default="estável")
    weekly_trend: Mapped[str] = mapped_column(String(30), default="monitorar")
    monthly_trend: Mapped[str] = mapped_column(String(30), default="monitorar")
    price_spread: Mapped[float] = mapped_column(Float, default=0)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (Index("ix_market_trend_lookup", "brand", "model", "year", "state", "created_at"),)
