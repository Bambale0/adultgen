"""Generation task and take models."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from adultgen.db.base import Base, CreatedAtMixin, jsonb_default, uuid_pk


class GenerationTask(Base, CreatedAtMixin):
    """Asynchronous provider generation task."""

    __tablename__ = "generation_tasks"
    __table_args__ = (UniqueConstraint("provider", "provider_task_id"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"))
    scene_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("scenes.id"))
    provider: Mapped[str] = mapped_column(Text, nullable=False)
    model_code: Mapped[str] = mapped_column(Text, nullable=False)
    operation: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    request_payload: Mapped[dict[str, object]] = jsonb_default()
    provider_task_id: Mapped[str | None] = mapped_column(Text)
    reserved_credits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    charged_credits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    technical_defect_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    error_code: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SceneTake(Base, CreatedAtMixin):
    """One provider result/take for a scene."""

    __tablename__ = "scene_takes"

    id: Mapped[uuid.UUID] = uuid_pk()
    generation_task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("generation_tasks.id"), nullable=False
    )
    scene_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scenes.id"), nullable=False)
    video_asset_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("media_assets.id"))
    image_asset_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("media_assets.id"))
    last_frame_asset_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("media_assets.id"))
    preview_asset_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("media_assets.id"))
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    quality_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    continuity_notes: Mapped[str | None] = mapped_column(Text)
