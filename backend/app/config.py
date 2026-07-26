from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "QuantStock AI"
    app_version: str = "1.0.0"
    environment: str = "development"
    log_level: str = "INFO"
    secret_key: str = "changeme-in-production-minimum-32chars"

    database_url: str = "postgresql://postgres:postgres@localhost:5432/quantstock"
    redis_url: str = "redis://localhost:6379/0"

    # Cache TTLs (seconds)
    cache_ttl_market_data: int = 60
    cache_ttl_technical: int = 300
    cache_ttl_fundamental: int = 3600
    cache_ttl_options: int = 120
    cache_ttl_news: int = 600

    # Optional API keys
    openai_api_key: Optional[str] = None
    news_api_key: Optional[str] = None

    # Risk-free rate for calculations
    risk_free_rate: float = 0.0525  # 10-yr US Treasury

    # Monte Carlo defaults
    mc_simulations: int = 10_000
    mc_steps: int = 252

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
