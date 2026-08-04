"""Profile, publication, feed, collection, and remix models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from adultgen.db.base import Base, CreatedAtMixin, TimestampMixin, jsonb_default, uuid_pk


class UserProfile(Base, TimestampMixin):
    """Public/private creator profile."""

    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False
    )
    public_id: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(Text)
    bio: Mapped[str | None] = mapped_column(Text)
    avatar_asset_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("media_assets.id"))
    visibility: Mapped[str] = mapped_column(Text, default="private", nullable=False)


class Publication(Base):
    """A user-published media item in profile or feed."""

    __tablename__ = "publications"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"))
    scene_take_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("scene_takes.id"))
    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("media_assets.id"), nullable=False)
    title: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    visibility: Mapped[str] = mapped_column(Text, nullable=False)
    is_explicit: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    blur_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allow_remix: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    prompt_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class FeedEvent(Base, CreatedAtMixin):
    """User interaction with a feed publication."""

    __tablename__ = "feed_events"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    publication_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("publications.id"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    extra: Mapped[dict[str, object]] = jsonb_default()


class PublicationLike(Base, CreatedAtMixin):
    """Like toggle represented by row existence."""

    __tablename__ = "publication_likes"
    __table_args__ = (UniqueConstraint("user_id", "publication_id"),)

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    publication_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("publications.id"), primary_key=True
    )


class SavedPublication(Base):
    """A publication saved into a user's Mini App collection."""

    __tablename__ = "saved_publications"
    __table_args__ = (UniqueConstraint("user_id", "publication_id"),)

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    publication_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("publications.id"), primary_key=True
    )
    saved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RemixSource(Base, CreatedAtMixin):
    """Links a cloned project to the feed publication it remixed."""

    __tablename__ = "remix_sources"

    id: Mapped[uuid.UUID] = uuid_pk()
    source_publication_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("publications.id"), nullable=False
    )
    new_project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    remixed_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
