from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./mcv_data_engine.sqlite3"
    fipe_base_url: str = "https://parallelum.com.br/fipe/api/v1/carros"
    collection_mode: str = "safe"
    max_requests_per_minute: int = 30
    user_agent: str = "MeuCarroValeDataEngine/1.0"
    enable_olx: bool = False
    enable_webmotors: bool = False
    enable_icarros: bool = False
    enable_mercadolivre: bool = False
    enable_kavak: bool = False
    export_formats: str = "parquet,csv"
    # FIPE: padrão seguro para execução longa.
    # Mantém FIPE_SYNC_SLEEP_SECONDS por compatibilidade e usa
    # FIPE_SYNC_BASE_SLEEP_SECONDS como novo controle principal.
    fipe_sync_sleep_seconds: float = 1.5
    fipe_sync_base_sleep_seconds: float = 1.5
    fipe_sync_timeout_seconds: int = 20
    fipe_sync_max_retries: int = 6
    fipe_sync_backoff_multiplier: float = 3
    fipe_sync_max_backoff_seconds: int = 180
    fipe_sync_429_cooldown_seconds: int = 300
    fipe_sync_max_429_before_cooldown: int = 5
    fipe_sync_enable_carros: bool = True
    fipe_sync_enable_motos: bool = True
    fipe_sync_enable_caminhoes: bool = True
    fipe_sync_mark_missing_inactive: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def safe_delay_seconds(self) -> float:
        return max(60 / max(self.max_requests_per_minute, 1), 0.5)


@lru_cache
def get_settings() -> Settings:
    return Settings()
