"""Subscription models for recurring credit grants."""

from __future__ import annotations

import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from adultgen.db.base import Base, TimestampMixin, uuid_pk


class UserSubscription(Base, TimestampMixin):
    """User subscription state for a plan-backed recurring credit bundle."""

    __tablename__ = "user_subscriptions"
    __table_args__ = (UniqueConstraint("user_id", "plan_code", "status"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    plan_code: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, default="active", index=True)
    provider: Mapped[str | None] = mapped_column(Text)
    provider_subscription_id: Mapped[str | None] = mapped_column(Text)
    current_period_start: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    current_period_end: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    cancel_at_period_end: Mapped[bool] = mapped_column(default=False, nullable=False)
    cancelled_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    last_granted_at: Mapped[object | None] = mapped_column(DateTime(timezone=True))


class SubscriptionCreditGrant(Base, TimestampMixin):
    """Idempotent record of credits granted for a subscription period."""

    __tablename__ = "subscription_credit_grants"
    __table_args__ = (UniqueConstraint("subscription_id", "period_start", "period_end"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("user_subscriptions.id"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    plan_code: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    credits_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    period_start: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False)
    wallet_entry_operation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, unique=True)
