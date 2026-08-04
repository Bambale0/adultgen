"""Media storage metadata models."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, Numeric, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from adultgen.db.base import Base, CreatedAtMixin, uuid_pk


class MediaAsset(Base, CreatedAtMixin):
    """Stored media object metadata.

    Binary files live in S3-compatible storage or Telegram. PostgreSQL stores only
    references and searchable metadata.
    """

    __tablename__ = "media_assets"
    __table_args__ = (UniqueConstraint("storage_bucket", "storage_key"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    owner_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    storage_bucket: Mapped[str] = mapped_column(Text, nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    media_type: Mapped[str] = mapped_column(Text, nullable=False)
    mime_type: Mapped[str] = mapped_column(Text, nullable=False)
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    duration_seconds: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    checksum_sha256: Mapped[str | None] = mapped_column(Text)
    telegram_file_id: Mapped[str | None] = mapped_column(Text)
    is_temporary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
