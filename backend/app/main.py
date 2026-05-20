from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import auth, vehicles, saas, search
from app.api.routes import fipe, market, intelligence
from app.vehicle_catalog.routes import catalog
from app.db.init_db import init_database


init_database()

app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in settings.backend_cors_origins.split(',')],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth.router, prefix="/api")
app.include_router(vehicles.router, prefix="/api")
app.include_router(saas.router, prefix="/api")
app.include_router(search.router, prefix="/api")
app.include_router(fipe.router, prefix="/api")
app.include_router(market.router, prefix="/api")
app.include_router(intelligence.router, prefix="/api")
app.include_router(catalog.router, prefix="/api")

@app.get("/health")
def health():
    return {"status":"ok", "app": settings.app_name, "env": settings.app_env, "app_mode": settings.app_mode.upper()}
