import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.session import Base
from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.market import FipePrice, MarketListing, ValuationRun, ValuationComparable, MarketListingHistory, MarketSnapshot, MarketPriceStats, MarketLiquidity, MarketCollectionJob
from app.vehicle_catalog.models import VehicleBrand, VehicleBrandAlias, VehicleModel, VehicleModelAlias, VehicleVersion, VehicleCatalogSyncLog, VehicleCatalogSyncJob

@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
