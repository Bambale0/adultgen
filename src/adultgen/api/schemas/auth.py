"""Authentication API schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class TelegramMiniAppAuthRequest(BaseModel):
    """Payload sent by Mini App after reading Telegram WebApp initData."""

    bot_username: str = Field(min_length=1, description="Telegram bot username that opened Mini App.")
    init_data: str = Field(min_length=1, description="Raw Telegram WebApp initData string.")
    start_payload: str | None = Field(default=None, description="Optional /start payload attribution.")


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
