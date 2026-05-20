from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Meu Carro Vale"
    app_env: str = "local"
    database_url: str = "sqlite:///./meu_carro_vale.db"
    jwt_secret: str = "dev-secret"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 14
    backend_cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5180,http://127.0.0.1:5180"
    demo_mode: bool = True
    app_mode: str = "DEMO"  # DEMO usa showcase; REAL exige FIPE/cache ou CSV real.
    fipe_cache_ttl_seconds: int = 43200
    min_comparable_score: int = 62
    use_data_engine_exports: bool = True
    data_engine_exports_path: str = Field(default="../mcv-data-engine/exports", validation_alias="MCV_DATA_ENGINE_EXPORTS_PATH")
    data_engine_mode: str = Field(default="api", validation_alias="MCV_DATA_ENGINE_MODE")
    data_engine_api_url: str = Field(default="http://127.0.0.1:8020", validation_alias="MCV_DATA_ENGINE_API_URL")

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
