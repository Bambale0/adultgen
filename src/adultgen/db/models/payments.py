"""Payment orders and immutable webhook capture models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    LargeBinary,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import Mapped, mapped_column

from adultgen.db.base import Base, TimestampMixin, jsonb_default, uuid_pk


class PaymentOrder(Base, TimestampMixin):
    """Internal payment order created before redirecting to a provider checkout."""

    __tablename__ = "payment_orders"
    __table_args__ = (UniqueConstraint("provider", "external_payment_id"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    external_payment_id: Mapped[str | None] = mapped_column(Text)
    checkout_token_hash: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    callback_token_hash: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    provider_checkout_url: Mapped[str | None] = mapped_column(Text)
    package_code: Mapped[str] = mapped_column(Text, nullable=False)
    amount_minor: Mapped[int] = mapped_column(BigInteger, nullable=False)
    currency: Mapped[str] = mapped_column(Text, nullable=False)
    credits_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PaymentWebhookRaw(Base):
    """Append-only raw payment webhook request.

    Raw data is stored before provider parsing or business mutation.
    """

    __tablename__ = "payment_webhook_raw"

    id: Mapped[uuid.UUID] = uuid_pk()
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    request_method: Mapped[str] = mapped_column(Text, nullable=False)
    request_path: Mapped[str,] = mapped_column(Text, nullable=False)
    query_string: Mapped[str | None] = mapped_column(Text)
    headers: Mapped[dict[str, object]] = jsonb_default()
    raw_body: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    source_ip: Mapped[str | None] = mapped_column(INET)
    body_sha256: Mapped[str] = mapped_column(Text, nullable=False)
    signature_valid: Mapped[bool | None] = mapped_column(Boolean)
    previous_event_hash: Mapped[str | None] = mapped_column(Text)
    event_hash: Mapped[str] = mapped_column(Text, unique=True, nullable=False)


class PaymentWebhookProcessing(Base, TimestampMixin):
    """Mutable processing status for a raw payment webhook."""

    __tablename__ = "payment_webhook_processing"

    id: Mapped[uuid.UUID] = uuid_pk()
    webhook_raw_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payment_webhook_raw.id"), unique=True, nullable=False
    )
    status: Mapped[str] = mapped_column(Text, nullable=False)
    attempt_count: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    payment_order_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("payment_orders.id")
    )
    last_error: Mapped[str | None] = mapped_column(Text)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
