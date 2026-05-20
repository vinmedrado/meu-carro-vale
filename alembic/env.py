from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

sys.path.insert(0, os.path.abspath("backend"))
from app.core.config import settings
from app.db.session import Base
from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.saas import Tenant, Role, TenantUser, Plan, Subscription, UsageEvent, ValuationReport, ReportExport, RefreshToken
from app.models.market import FipePrice, MarketListing, ValuationRun, ValuationComparable, MarketListingHistory, MarketSnapshot, MarketPriceStats, MarketLiquidity, MarketCollectionJob
from app.vehicle_catalog.models import VehicleBrand, VehicleBrandAlias, VehicleModel, VehicleModelAlias, VehicleVersion, VehicleCatalogSyncLog

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(url=settings.database_url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(config.get_section(config.config_ini_section), prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
