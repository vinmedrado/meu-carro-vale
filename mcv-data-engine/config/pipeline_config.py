from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PipelineConfig:
    batch_size: int = 2000
    retries: int = 1
    enable_cache: bool = True
    safe_mode: bool = True
    export_dir: Path = Path("exports")
    log_dir: Path = Path("logs/pipeline")
    default_input: Path = Path("sample_market_listings.csv")
    fail_on_validation_error: bool = False


def get_pipeline_config() -> PipelineConfig:
    return PipelineConfig()
