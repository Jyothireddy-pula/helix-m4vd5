from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./wind_forecast.db"
    DATABASE_URL_SYNC: str = "sqlite:///./wind_forecast.db"

    # Elexon API
    ELEXON_BASE_URL: str = "https://data.elexon.co.uk/bmrs/api/v1"
    ELEXON_TIMEOUT_CONNECT: float = 10.0
    ELEXON_TIMEOUT_READ: float = 60.0
    ELEXON_MAX_RETRIES: int = 3
    ELEXON_CACHE_TTL_SECONDS: int = 3600

    # Analysis
    ANALYSIS_START: str = "2026-01-01"
    ANALYSIS_END: str = "2026-01-31"
    DEFAULT_DECISION_CUTOFF_HOUR: int = 16  # 16:00 UTC on day-1
    DEFAULT_DECISION_CUTOFF_MINUTE: int = 0

    # App
    CORS_ORIGINS: list[str] = ["*"]
    INGESTION_SECRET: Optional[str] = None

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
