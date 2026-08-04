"""User identity and Telegram channel application services."""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.config import Settings
from adultgen.db.models.users import TelegramChannel, User, UserChannelActivity
from adultgen.integrations.telegram.mini_app_auth import TelegramMiniAppUser


class UserServiceError(ValueError):
    """Raised when user/channel service operations fail."""


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    """Canonical user returned by auth service."""

    id: uuid.UUID
    telegram_user_id: int
    is_blocked: bool
    can_generate: bool
    can_publish_profile: bool
    can_publish_feed: bool
    can_use_payments: bool


class BotTokenResolver:
    """Resolve bot tokens from secret references.

    MVP supports env-based secret refs. Production can replace this class with a
    secret manager implementation without changing the auth router.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def resolve(self, secret_ref: str) -> str:
        """Resolve a Telegram bot token from a channel secret reference."""

        if secret_ref == "env:TELEGRAM_DEFAULT_BOT_TOKEN":
            return self._settings.telegram_default_bot_token
        if secret_ref.startswith("env:"):
            env_name = secret_ref.removeprefix("env:")
            value = os.getenv(env_name)
            if value:
                return value
            raise UserServiceError(f"Environment secret {env_name!r} is not configured.")
        raise UserServiceError(f"Unsupported bot token secret reference: {secret_ref!r}.")


async def get_active_telegram_channel(
    session: AsyncSession,
    *,
    bot_username: str,
) -> TelegramChannel:
    """Return an active Telegram channel by bot username."""

    normalized_username = bot_username.removeprefix("@").lower()
    result = await session.execute(
        select(TelegramChannel).where(
            TelegramChannel.bot_username == normalized_username,
            TelegramChannel.status == "active",
        )
    )
    channel = result.scalar_one_or_none()
    if channel is None:
        raise UserServiceError(f"Active Telegram channel {normalized_username!r} not found.")
    return channel


async def upsert_user_from_telegram(
    session: AsyncSession,
    *,
    telegram_user: TelegramMiniAppUser,
) -> AuthenticatedUser:
    """Create or update canonical user by Telegram user id."""

    user_values = {
        "telegram_user_id": telegram_user.id,
        "username": telegram_user.username,
        "first_name": telegram_user.first_name,
        "last_name": telegram_user.last_name,
        "language_code": telegram_user.language_code,
    }
    insert_stmt = insert(User).values(**user_values)
    update_values = {
        key: insert_stmt.excluded[key]
        for key in ("username", "first_name", "last_name", "language_code")
    }

    await session.execute(
        insert_stmt.on_conflict_do_update(
            index_elements=[User.telegram_user_id],
            set_=update_values,
        )
    )

    result = await session.execute(
        select(User).where(User.telegram_user_id == telegram_user.id)
    )
    user = result.scalar_one()
    return AuthenticatedUser(
        id=user.id,
        telegram_user_id=user.telegram_user_id,
        is_blocked=user.is_blocked,
        can_generate=user.can_generate,
        can_publish_profile=user.can_publish_profile,
        can_publish_feed=user.can_publish_feed,
        can_use_payments=user.can_use_payments,
    )


async def record_user_channel_activity(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    telegram_channel_id: uuid.UUID,
    telegram_chat_id: int | None,
    start_payload: str | None,
) -> None:
    """Upsert the user's interaction with a Telegram channel mirror."""

    now = datetime.now(UTC)
    insert_stmt = insert(UserChannelActivity).values(
        user_id=user_id,
        telegram_channel_id=telegram_channel_id,
        telegram_chat_id=telegram_chat_id,
        first_seen_at=now,
        last_seen_at=now,
        start_payload=start_payload,
    )

    await session.execute(
        insert_stmt.on_conflict_do_update(
            index_elements=[
                UserChannelActivity.user_id,
                UserChannelActivity.telegram_channel_id,
            ],
            set_={
                "telegram_chat_id": insert_stmt.excluded.telegram_chat_id,
                "last_seen_at": now,
                "start_payload": insert_stmt.excluded.start_payload,
            },
        )
    )
