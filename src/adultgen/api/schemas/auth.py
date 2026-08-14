"""Authentication API schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class TelegramMiniAppAuthRequest(BaseModel):
    """Payload sent by Mini App after reading Telegram WebApp initData."""

    bot_username: str = Field(min_length=1, description="Telegram bot username that opened Mini App.")
    init_data: str = Field(min_length=1, description="Raw Telegram WebApp initData string.")
    start_payload: str | None = Field(default=None, description="Optional /start payload attribution.")


class GoogleAuthRequest(BaseModel):
    """Google Identity Services ID token exchange payload."""

    credential: str = Field(min_length=32, description="Google-signed ID token returned by GIS.")
    referral_payload: str | None = Field(default=None, max_length=128)


class TelegramLoginAuthRequest(BaseModel):
    """Signed Telegram Login Widget callback payload."""

    id: int = Field(gt=0)
    first_name: str = Field(min_length=1, max_length=120)
    last_name: str | None = Field(default=None, max_length=120)
    username: str | None = Field(default=None, max_length=64)
    photo_url: str | None = Field(default=None, max_length=2_048)
    auth_date: int = Field(gt=0)
    hash: str = Field(min_length=64, max_length=64)
    referral_payload: str | None = Field(default=None, max_length=128)


class UserCapabilityResponse(BaseModel):
    """User permission flags needed by Mini App navigation."""

    can_generate: bool
    can_publish_profile: bool
    can_publish_feed: bool
    can_use_payments: bool


class TelegramMiniAppAuthResponse(BaseModel):
    """Successful Mini App auth response."""

    access_token: str
    token_type: str = "bearer"
    user_id: uuid.UUID
    telegram_user_id: int
    is_blocked: bool
    capabilities: UserCapabilityResponse


class WebsiteAuthResponse(TelegramMiniAppAuthResponse):
    """Successful standalone website provider exchange."""

    provider: str
    email: str | None = None
    display_name: str
