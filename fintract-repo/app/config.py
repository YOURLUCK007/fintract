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

    # ── Email via Brevo (HTTPS — free, no domain needed) ─────────────────────
    # Render blocks outbound SMTP, so we use Brevo's HTTP API instead.
    # Sign up free at https://brevo.com (300 emails/day free).
    # Verify your sender email under Senders & IP → Senders, then get an
    # API key from profile menu → SMTP & API → API Keys.
    brevo_api_key: str = ""
    brevo_from_email: str = ""  # must match a verified sender in your Brevo account

    # Public base URL for verification links (no trailing slash).
    # In production set this to your real domain: https://fintract.app
    app_base_url: str = "http://localhost:8000"

    # ── Stripe ───────────────────────────────────────────────────────────────
    # Get keys from https://dashboard.stripe.com/apikeys
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""
    # Price ID for the FinTract Pro monthly plan (create in Stripe dashboard)
    stripe_pro_price_id: str = ""

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
