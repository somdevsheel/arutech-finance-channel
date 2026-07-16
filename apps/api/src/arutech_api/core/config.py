from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "test", "staging", "production"]

_INSECURE_DEV_DEFAULT = "insecure-development-only-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    ENVIRONMENT: Environment = "development"
    DEBUG: bool = False

    APP_NAME: str = "Arutech Finance API"
    APP_VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"

    # Symmetric secret for non-JWT crypto needs (e.g. CSRF tokens).
    SECRET_KEY: str = _INSECURE_DEV_DEFAULT

    # RS256 keypair (PEM contents, not file paths) for JWT signing/verification.
    JWT_PRIVATE_KEY: str = ""
    JWT_PUBLIC_KEY: str = ""
    JWT_ALGORITHM: str = "RS256"
    JWT_ISSUER: str = "arutech-finance-platform"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    OTP_EXPIRE_MINUTES: int = 10

    DATABASE_URL: str = "postgresql+asyncpg://arutech:arutech@localhost:5432/arutech"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_ECHO: bool = False

    REDIS_URL: str = "redis://localhost:6379/0"

    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None

    CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    OTEL_SERVICE_NAME: str = "arutech-api"
    OTEL_EXPORTER_OTLP_ENDPOINT: str | None = None

    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "arutech"
    S3_SECRET_KEY: str = _INSECURE_DEV_DEFAULT
    S3_BUCKET_NAME: str = "arutech-documents"
    S3_REGION: str = "us-east-1"

    LOG_LEVEL: str = "INFO"
    LOG_JSON: bool = True

    RATE_LIMIT_DEFAULT: str = "100/minute"
    # Storage backend for the request-rate limiter (a `limits`-library URI,
    # e.g. "memory://" for tests/single-process). Defaults to REDIS_URL so
    # limits are shared across instances in every real environment.
    RATE_LIMIT_STORAGE_URI: str | None = None

    @property
    def rate_limit_storage_uri(self) -> str:
        return self.RATE_LIMIT_STORAGE_URI or self.REDIS_URL

    @property
    def celery_broker_url(self) -> str:
        return self.CELERY_BROKER_URL or self.REDIS_URL

    @property
    def celery_result_backend(self) -> str:
        return self.CELERY_RESULT_BACKEND or self.REDIS_URL

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache
def get_settings() -> Settings:
    settings = Settings()

    if settings.ENVIRONMENT in ("staging", "production"):
        insecure_fields = [
            name
            for name, value in (
                ("SECRET_KEY", settings.SECRET_KEY),
                ("S3_SECRET_KEY", settings.S3_SECRET_KEY),
            )
            if value == _INSECURE_DEV_DEFAULT
        ]
        if insecure_fields:
            raise RuntimeError(
                "Refusing to start with insecure default secrets in "
                f"{settings.ENVIRONMENT}: {', '.join(insecure_fields)}. "
                "Set them via environment variables or a mounted secrets store."
            )
        if not settings.JWT_PRIVATE_KEY or not settings.JWT_PUBLIC_KEY:
            raise RuntimeError(
                f"JWT_PRIVATE_KEY and JWT_PUBLIC_KEY must be set in {settings.ENVIRONMENT}."
            )

    return settings


settings = get_settings()
