"""Admin audit log models."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from adultgen.db.base import Base, CreatedAtMixin, jsonb_default, uuid_pk


class AdminAuditEvent(Base, CreatedAtMixin):
    """Append-only audit event for dangerous admin actions."""

    __tablename__ = "admin_audit_events"

    id: Mapped[uuid.UUID] = uuid_pk()
    admin_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    target_type: Mapped[str] = mapped_column(Text, nullable=False)
    target_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    action: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    before_state: Mapped[dict[str, object]] = jsonb_default()
    after_state: Mapped[dict[str, object]] = jsonb_default()
