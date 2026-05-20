from datetime import datetime, date
from sqlalchemy import Boolean, Date, DateTime, Float, Index, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from config.settings import get_settings


class Base(DeclarativeBase):
    pass


class MarketListing(Base):
    __tablename__ = "market_listings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    marca: Mapped[str | None] = mapped_column(String(120), index=True)
    modelo: Mapped[str | None] = mapped_column(String(180), index=True)
    versao: Mapped[str | None] = mapped_column(String(220), index=True)
    ano: Mapped[int | None] = mapped_column(Integer, index=True)
    km: Mapped[int | None] = mapped_column(Integer)
    preco: Mapped[float | None] = mapped_column(Float, index=True)
    cidade: Mapped[str | None] = mapped_column(String(120), index=True)
    estado: Mapped[str | None] = mapped_column(String(2), index=True)
    fonte: Mapped[str] = mapped_column(String(60), index=True)
    url: Mapped[str | None] = mapped_column(Text)
    data_coleta: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    data_publicacao: Mapped[date | None] = mapped_column(Date)
    vendedor_tipo: Mapped[str | None] = mapped_column(String(60))
    cambio: Mapped[str | None] = mapped_column(String(80))
    combustivel: Mapped[str | None] = mapped_column(String(80))
    cor: Mapped[str | None] = mapped_column(String(60))
    placa_parcial: Mapped[str | None] = mapped_column(String(20), index=True)
    vendedor_id: Mapped[str | None] = mapped_column(String(120), index=True)
    validation_errors: Mapped[str | None] = mapped_column(Text)
    validation_warnings: Mapped[str | None] = mapped_column(Text)
    normalization_status: Mapped[str | None] = mapped_column(String(80))
    duplicate_confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    normalizado: Mapped[bool] = mapped_column(Boolean, default=False)
    qualidade_dado: Mapped[float] = mapped_column(Float, default=0.0)
    duplicado: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    hash_similaridade: Mapped[str | None] = mapped_column(String(64), index=True)


Index("ix_listing_lookup", MarketListing.marca, MarketListing.modelo, MarketListing.ano, MarketListing.estado)


class MarketSnapshot(Base):
    __tablename__ = "market_snapshots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    marca: Mapped[str | None] = mapped_column(String(120), index=True)
    modelo: Mapped[str | None] = mapped_column(String(180), index=True)
    versao: Mapped[str | None] = mapped_column(String(220), index=True)
    ano: Mapped[int | None] = mapped_column(Integer, index=True)
    regiao: Mapped[str | None] = mapped_column(String(80), index=True)
    data_snapshot: Mapped[date] = mapped_column(Date, default=date.today, index=True)
    qtd_anuncios: Mapped[int] = mapped_column(Integer, default=0)
    preco_mediano: Mapped[float | None] = mapped_column(Float)
    preco_p25: Mapped[float | None] = mapped_column(Float)
    preco_p75: Mapped[float | None] = mapped_column(Float)
    dispersao_preco: Mapped[float | None] = mapped_column(Float)
    preco_medio: Mapped[float | None] = mapped_column(Float)
    preco_p10: Mapped[float | None] = mapped_column(Float)
    preco_p90: Mapped[float | None] = mapped_column(Float)
    estado: Mapped[str | None] = mapped_column(String(2), index=True)
    cidade: Mapped[str | None] = mapped_column(String(120), index=True)
    semana: Mapped[int | None] = mapped_column(Integer, index=True)
    mes: Mapped[str | None] = mapped_column(String(7), index=True)
    liquidez: Mapped[str | None] = mapped_column(String(40))
    temperatura_mercado: Mapped[str | None] = mapped_column(String(80))


class VehicleCatalog(Base):
    __tablename__ = "vehicle_catalog"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    marca: Mapped[str] = mapped_column(String(120), index=True)
    modelo: Mapped[str] = mapped_column(String(180), index=True)
    versao: Mapped[str | None] = mapped_column(String(220))
    ano: Mapped[int | None] = mapped_column(Integer, index=True)
    codigo_fipe: Mapped[str | None] = mapped_column(String(40), index=True)
    preco_fipe: Mapped[float | None] = mapped_column(Float)
    combustivel: Mapped[str | None] = mapped_column(String(80))
    mes_referencia: Mapped[str | None] = mapped_column(String(80))
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class VehicleAlias(Base):
    __tablename__ = "vehicle_aliases"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    original: Mapped[str] = mapped_column(String(220), index=True)
    normalizado: Mapped[str] = mapped_column(String(220), index=True)
    tipo: Mapped[str] = mapped_column(String(40), default="modelo")


class CollectionJob(Base):
    __tablename__ = "collection_jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fonte: Mapped[str] = mapped_column(String(60), index=True)
    status: Mapped[str] = mapped_column(String(40), default="pending", index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    records_collected: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)


class ListingDuplicate(Base):
    __tablename__ = "listing_duplicates"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    listing_id: Mapped[int] = mapped_column(Integer, index=True)
    duplicate_of_id: Mapped[int] = mapped_column(Integer, index=True)
    reason: Mapped[str] = mapped_column(String(120))
    similarity: Mapped[float] = mapped_column(Float)


class MarketLiquidity(Base):
    __tablename__ = "market_liquidity"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    marca: Mapped[str | None] = mapped_column(String(120), index=True)
    modelo: Mapped[str | None] = mapped_column(String(180), index=True)
    ano: Mapped[int | None] = mapped_column(Integer, index=True)
    regiao: Mapped[str | None] = mapped_column(String(80), index=True)
    qtd_anuncios: Mapped[int] = mapped_column(Integer, default=0)
    dispersao_preco: Mapped[float | None] = mapped_column(Float)
    saturacao: Mapped[float | None] = mapped_column(Float)
    pressao_mercado: Mapped[float | None] = mapped_column(Float)
    volume_regional: Mapped[float | None] = mapped_column(Float)
    estabilidade: Mapped[float | None] = mapped_column(Float)
    velocidade_venda_estimada: Mapped[str | None] = mapped_column(String(80))
    temperatura_mercado: Mapped[str | None] = mapped_column(String(80))
    tendencia: Mapped[str | None] = mapped_column(String(80))
    liquidity_level: Mapped[str | None] = mapped_column(String(40))
    calculated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MarketQuality(Base):
    __tablename__ = "market_quality"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    fonte: Mapped[str | None] = mapped_column(String(60), index=True)
    marca: Mapped[str | None] = mapped_column(String(120), index=True)
    modelo: Mapped[str | None] = mapped_column(String(180), index=True)
    estado: Mapped[str | None] = mapped_column(String(2), index=True)
    total_registros: Mapped[int] = mapped_column(Integer, default=0)
    qualidade_media: Mapped[float | None] = mapped_column(Float)
    registros_com_erro: Mapped[int] = mapped_column(Integer, default=0)
    campos_faltantes: Mapped[str | None] = mapped_column(Text)
    calculated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MarketTrend(Base):
    __tablename__ = "market_trends"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    marca: Mapped[str | None] = mapped_column(String(120), index=True)
    modelo: Mapped[str | None] = mapped_column(String(180), index=True)
    ano: Mapped[int | None] = mapped_column(Integer, index=True)
    regiao: Mapped[str | None] = mapped_column(String(80), index=True)
    janela: Mapped[str] = mapped_column(String(40), default="mensal")
    variacao_percentual: Mapped[float | None] = mapped_column(Float)
    tendencia: Mapped[str | None] = mapped_column(String(80))
    calculated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)



class VehicleBrand(Base):
    __tablename__ = "vehicle_brands"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vehicle_type: Mapped[str] = mapped_column(String(30), index=True)
    fipe_brand_code: Mapped[str] = mapped_column(String(50), index=True)
    canonical_name: Mapped[str] = mapped_column(String(160), index=True)
    normalized_name: Mapped[str] = mapped_column(String(160), index=True)
    source: Mapped[str] = mapped_column(String(40), default="FIPE", index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


Index("ux_vehicle_brand_fipe", VehicleBrand.vehicle_type, VehicleBrand.fipe_brand_code, unique=True)


class VehicleModelMaster(Base):
    __tablename__ = "vehicle_models"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    brand_id: Mapped[int] = mapped_column(Integer, index=True)
    vehicle_type: Mapped[str] = mapped_column(String(30), index=True)
    fipe_model_code: Mapped[str] = mapped_column(String(50), index=True)
    canonical_name: Mapped[str] = mapped_column(String(220), index=True)
    normalized_name: Mapped[str] = mapped_column(String(220), index=True)
    source: Mapped[str] = mapped_column(String(40), default="FIPE", index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


Index("ux_vehicle_model_fipe", VehicleModelMaster.vehicle_type, VehicleModelMaster.brand_id, VehicleModelMaster.fipe_model_code, unique=True)


class VehicleVersion(Base):
    __tablename__ = "vehicle_versions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    brand_id: Mapped[int] = mapped_column(Integer, index=True)
    model_id: Mapped[int] = mapped_column(Integer, index=True)
    vehicle_type: Mapped[str] = mapped_column(String(30), index=True)
    fipe_year_code: Mapped[str] = mapped_column(String(50), index=True)
    fipe_code: Mapped[str | None] = mapped_column(String(50), index=True)
    year: Mapped[int | None] = mapped_column(Integer, index=True)
    fuel: Mapped[str | None] = mapped_column(String(80), index=True)
    version_name: Mapped[str | None] = mapped_column(String(260), index=True)
    normalized_version_name: Mapped[str | None] = mapped_column(String(260), index=True)
    reference_month: Mapped[str | None] = mapped_column(String(100), index=True)
    fipe_price: Mapped[float | None] = mapped_column(Float)
    source: Mapped[str] = mapped_column(String(40), default="FIPE", index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


Index("ux_vehicle_version_fipe", VehicleVersion.vehicle_type, VehicleVersion.model_id, VehicleVersion.fipe_year_code, VehicleVersion.fipe_code, unique=True)


class VehicleCatalogSyncRun(Base):
    __tablename__ = "vehicle_catalog_sync_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_type: Mapped[str] = mapped_column(String(40), index=True)
    vehicle_type: Mapped[str | None] = mapped_column(String(30), index=True)
    status: Mapped[str] = mapped_column(String(40), default="running", index=True)
    total_brands_found: Mapped[int] = mapped_column(Integer, default=0)
    total_models_found: Mapped[int] = mapped_column(Integer, default=0)
    total_versions_found: Mapped[int] = mapped_column(Integer, default=0)
    new_brands: Mapped[int] = mapped_column(Integer, default=0)
    new_models: Mapped[int] = mapped_column(Integer, default=0)
    new_versions: Mapped[int] = mapped_column(Integer, default=0)
    updated_brands: Mapped[int] = mapped_column(Integer, default=0)
    updated_models: Mapped[int] = mapped_column(Integer, default=0)
    updated_versions: Mapped[int] = mapped_column(Integer, default=0)
    skipped_existing: Mapped[int] = mapped_column(Integer, default=0)
    failed_items: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)
    error_message: Mapped[str | None] = mapped_column(Text)


def get_engine():
    return create_engine(get_settings().database_url, future=True)


def init_db(engine=None):
    engine = engine or get_engine()
    Base.metadata.create_all(engine)
    return engine


def get_session_factory(engine=None):
    engine = engine or get_engine()
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)
