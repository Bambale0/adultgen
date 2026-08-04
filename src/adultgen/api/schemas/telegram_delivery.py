"""Telegram delivery API schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

from adultgen.telegram_gateway.result_delivery import TelegramDeliveryMediaKind


class TelegramResultDeliveryRequest(BaseModel):
    """Internal request to deliver one generation result to a Telegram chat."""

    bot_username: str = Field(min_length=1)
    chat_id: int
    media_kind: TelegramDeliveryMediaKind
    caption: str = Field(min_length=1)
    media_url: str | None = None
    telegram_file_id: str | None = None
    include_mini_app_buttons: bool = True
    profile_public_id: str | None = None
    referral_code: str | None = None


class TelegramResultDeliveryResponse(BaseModel):
    """Successful result delivery response."""

    ok: bool
    bot_username: str
    chat_id: int
    telegram_message_id: int
    media_kind: TelegramDeliveryMediaKind
