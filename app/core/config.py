from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Postgres
    database_url: str = "postgresql+asyncpg://valuation:valuation@db:5432/valuation"

    # Celery / Redis
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"

    # Auth
    jwt_secret_key: str = "change-me-in-local-env"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # Screener.in scraping
    screener_base_url: str = "https://www.screener.in"
    scrape_delay_seconds: float = 2.0
    scrape_user_agent: str = "Mozilla/5.0"

    # Local storage
    exports_dir: str = "/app/data/exports"

    # App
    app_env: str = "local"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
