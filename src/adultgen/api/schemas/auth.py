"""Authentication API schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, EmailStr, Field


class TelegramMiniAppAuthRequest(BaseModel):
    """Payload sent by Mini App after reading Telegram WebApp initData."""

    bot_username: str = Field(min_length=1, description="Telegram bot username that opened Mini App.")
    init_data: str = Field(min_length=1, description="Raw Telegram WebApp initData string.")
    start_payload: str | None = Field(default=None, description="Optional /start payload attribution.")


class WebSessionAuthRequest(BaseModel):
    """Website-first auth payload for the standalone web app MVP."""

    email: EmailStr = Field(description="Website account email used for the MVP web session.")
    display_name: str | None = Field(default=None, max_length=80)
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


class WebSessionAuthResponse(TelegramMiniAppAuthResponse):
    """Successful standalone website auth response."""

    email: EmailStr
    display_name: str
