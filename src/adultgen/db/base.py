"""SQLAlchemy base types and mixins."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def uuid_pk() -> Mapped[uuid.UUID]:
    """Return a UUID primary-key mapped column."""

    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def now_utc() -> datetime:
    """Return timezone-aware UTC timestamp for Python-side defaults."""

    return datetime.now(UTC)


class TimestampMixin:
    """Created/updated timestamps for mutable domain entities."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now_utc,
        onupdate=now_utc,
        server_default=func.now(),
        nullable=False,
    )


class CreatedAtMixin:
    """Created timestamp for append-only records."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=now_utc, server_default=func.now(), nullable=False
    )


def jsonb_default() -> Mapped[Any]:
    """Return a JSONB column with an empty object default.

    Different domains use this helper for dict-shaped payloads and list-shaped
    button arrays. The database type is still JSONB; validation belongs to
    Pydantic schemas and domain services.
    """

    return mapped_column(JSONB, default=dict, server_default="{}", nullable=False)
