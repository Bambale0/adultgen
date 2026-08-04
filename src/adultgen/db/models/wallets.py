"""Wallet and append-only ledger models."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from adultgen.db.base import Base, CreatedAtMixin, TimestampMixin, jsonb_default, uuid_pk


class Wallet(Base, TimestampMixin):
    """User credit wallet with cached balances."""

    __tablename__ = "wallets"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False
    )
    currency: Mapped[str] = mapped_column(Text, default="credits", nullable=False)
    cached_available_balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cached_reserved_balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class WalletEntry(Base, CreatedAtMixin):
    """Append-only wallet operation entry.

    The wallet balance is reconstructed from this table. Cached wallet balances are
    convenience projections, not the source of truth.
    """

    __tablename__ = "wallet_entries"
    __table_args__ = (UniqueConstraint("operation_id", "entry_type", "bucket"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    wallet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("wallets.id"), nullable=False, index=True
    )
    operation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    entry_type: Mapped[str] = mapped_column(Text, nullable=False)
    bucket: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)

    generation_task_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    payment_order_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    admin_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    reason: Mapped[str | None] = mapped_column(Text)
    extra: Mapped[dict[str, object]] = jsonb_default()
