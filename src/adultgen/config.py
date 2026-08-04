"""Application settings.

Settings are intentionally centralized so bot mirrors, billing providers,
generation providers, and storage can be configured without changing domain code.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="local", alias="APP_ENV")
    app_name: str = Field(default="adultgen", alias="APP_NAME")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")

    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = Field(alias="REDIS_URL")

    s3_endpoint_url: str = Field(alias="S3_ENDPOINT_URL")
    s3_access_key: str = Field(alias="S3_ACCESS_KEY")
    s3_secret_key: str = Field(alias="S3_SECRET_KEY")
    s3_temp_bucket: str = Field(default="media-temporary", alias="S3_TEMP_BUCKET")
    s3_published_bucket: str = Field(default="media-published", alias="S3_PUBLISHED_BUCKET")
    s3_references_bucket: str = Field(default="media-references", alias="S3_REFERENCES_BUCKET")
    s3_webhook_bucket: str = Field(default="webhook-archive", alias="S3_WEBHOOK_BUCKET")

    telegram_default_webhook_secret: str = Field(alias="TELEGRAM_DEFAULT_WEBHOOK_SECRET")

    kie_api_base_url: str = Field(default="https://api.kie.ai", alias="KIE_API_BASE_URL")
    kie_api_key: str = Field(alias="KIE_API_KEY")

    billing_base_url: str = Field(alias="BILLING_BASE_URL")
    sharpay_api_key: str = Field(alias="SHARPAY_API_KEY")
    crocopay_api_key: str = Field(alias="CROCOPAY_API_KEY")
    crocopay_secret: str = Field(alias="CROCOPAY_SECRET")

    jwt_secret: str = Field(alias="JWT_SECRET")
    mini_app_auth_max_age_seconds: int = Field(default=86_400, alias="MINI_APP_AUTH_MAX_AGE_SECONDS")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()  # type: ignore[call-arg]
