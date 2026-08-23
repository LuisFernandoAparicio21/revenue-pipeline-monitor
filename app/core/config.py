from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_ENV: Literal["development", "staging", "production"] = "development"
    APP_SECRET_KEY: str
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    API_V1_PREFIX: str = "/api/v1"

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_POOL_MAX_CONNECTIONS: int = 20
    IDEMPOTENCY_TTL_SECONDS: int = 86400

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CELERY_TASK_MAX_RETRIES: int = 5
    CELERY_TASK_DEFAULT_RETRY_DELAY: int = 60

    # Stripe
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    STRIPE_WEBHOOK_TOLERANCE_SECONDS: int = 300
    STRIPE_API_VERSION: str = "2023-10-16"

    # HubSpot OAuth
    HUBSPOT_CLIENT_ID: str
    HUBSPOT_CLIENT_SECRET: str
    HUBSPOT_REDIRECT_URI: str = "http://localhost:8000/api/v1/oauth/hubspot/callback"
    HUBSPOT_SCOPES: str = "crm.objects.contacts.write crm.objects.deals.write oauth"

    # HubSpot Config
    HUBSPOT_API_BASE_URL: str = "https://api.hubapi.com"
    HUBSPOT_REQUESTS_PER_SECOND: int = 10
    HUBSPOT_DAILY_LIMIT: int = 250000
    HUBSPOT_DEAL_PIPELINE_ID: str = "default"
    HUBSPOT_DEAL_STAGE_NEW: str = "appointmentscheduled"
    HUBSPOT_DEAL_STAGE_PAID: str = "closedwon"
    HUBSPOT_DEAL_STAGE_CHURNED: str = "closedlost"

    # Anthropic / LLM
    ANTHROPIC_API_KEY: str
    LLM_MODEL: str = "claude-sonnet-4-6"
    LLM_MAX_TOKENS: int = 1024
    LLM_ENRICHMENT_ENABLED: bool = True
    LLM_CACHE_TTL_DAYS: int = 30

    # Security
    ENCRYPTION_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # HTTP Client
    HTTP_TIMEOUT_SECONDS: int = 30
    HTTP_MAX_RETRIES: int = 3
    HTTP_RETRY_BACKOFF_FACTOR: float = 2.0

    # Monitoring
    SENTRY_DSN: str = ""


settings = Settings()
