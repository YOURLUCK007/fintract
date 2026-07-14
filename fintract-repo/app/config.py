"""Application configuration loaded from environment variables."""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "FinTract API"
    environment: str = "development"

    # Default to a local SQLite file so the app runs with zero infrastructure.
    # In docker-compose this is overridden with a PostgreSQL URL.
    database_url: str = "sqlite:///./fintract.db"

    # JWT / auth
    secret_key: str = "change-me-in-production-please-use-a-long-random-string"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24h

    # Redis (optional cache / rate-limit backend)
    redis_url: str = ""

    # Rate limiting (requests per window per client)
    rate_limit_requests: int = 240
    rate_limit_window_seconds: int = 60

    # CORS
    cors_origins: str = "*"

    # Base monthly income used for demo seeding (INR)
    default_currency: str = "INR"

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
