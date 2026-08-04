"""Referral relation, partner wallet, commissions, and payouts."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from adultgen.db.base import Base, CreatedAtMixin, uuid_pk


class ReferralRelation(Base):
    """One immutable referral attribution for a referred user."""

    __tablename__ = "referral_relations"

    id: Mapped[uuid.UUID] = uuid_pk()
    referrer_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    referred_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False
    )
    attributed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    attribution_source: Mapped[str | None] = mapped_column(Text)
    first_payment_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    commission_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PartnerWallet(Base):
    """Money-denominated partner wallet projection."""

    __tablename__ = "partner_wallets"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False
    )
    pending_amount_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    available_amount_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    frozen_amount_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    paid_amount_minor: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    currency: Mapped[str] = mapped_column(Text, default="RUB", nullable=False)


class PartnerCommission(Base, CreatedAtMixin):
    """One commission entry created from a referred payment."""

    __tablename__ = "partner_commissions"

    id: Mapped[uuid.UUID] = uuid_pk()
    referrer_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    referred_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    payment_order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payment_orders.id"), nullable=False
    )
    percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    available_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PartnerPayoutRequest(Base):
    """Manual partner payout request."""

    __tablename__ = "partner_payout_requests"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    payout_method: Mapped[str | None] = mapped_column(Text)
    payout_details_encrypted: Mapped[str | None] = mapped_column(Text)
    admin_comment: Mapped[str | None] = mapped_column(Text)
    external_transfer_id: Mapped[str | None] = mapped_column(Text)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
