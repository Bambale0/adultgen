"""User identity, Telegram channels, and adult consent models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from adultgen.db.base import Base, CreatedAtMixin, TimestampMixin, uuid_pk


class User(Base, TimestampMixin):
    """Canonical platform user keyed by Telegram user id."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = uuid_pk()
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(Text)
    first_name: Mapped[str | None] = mapped_column(Text)
    last_name: Mapped[str | None] = mapped_column(Text)
    language_code: Mapped[str | None] = mapped_column(Text)

    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    can_generate: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_publish_profile: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_publish_feed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    can_use_payments: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class TelegramChannel(Base, TimestampMixin):
    """One connected Telegram bot mirror/channel."""

    __tablename__ = "telegram_channels"

    id: Mapped[uuid.UUID] = uuid_pk()
    bot_username: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    secret_ref: Mapped[str] = mapped_column(Text, nullable=False)
    webhook_secret_hash: Mapped[str] = mapped_column(Text, nullable=False)
    mini_app_url: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False)


class UserChannelActivity(Base):
    """Tracks user interaction with bot channels without owning identity by channel."""

    __tablename__ = "user_channel_activity"
    __table_args__ = (UniqueConstraint("user_id", "telegram_channel_id"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    telegram_channel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("telegram_channels.id"), nullable=False
    )
    telegram_chat_id: Mapped[int | None] = mapped_column(BigInteger)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    start_payload: Mapped[str | None] = mapped_column(Text)


class AdultConsent(Base, CreatedAtMixin):
    """Recorded 18+ policy acceptance."""

    __tablename__ = "adult_consents"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    policy_version: Mapped[str] = mapped_column(Text, nullable=False)
    source_channel_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("telegram_channels.id")
    )
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
