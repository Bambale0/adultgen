"""Admin audit helpers."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.db.models.audit import AdminAuditEvent


async def record_admin_audit_event(
    session: AsyncSession,
    *,
    target_type: str,
    action: str,
    reason: str | None = None,
    target_id: uuid.UUID | None = None,
    admin_user_id: uuid.UUID | None = None,
    before_state: dict[str, object] | None = None,
    after_state: dict[str, object] | None = None,
) -> AdminAuditEvent:
    """Append one admin audit event."""

    event = AdminAuditEvent(
        admin_user_id=admin_user_id,
        target_type=target_type,
        target_id=target_id,
        action=action,
        reason=reason,
        before_state=before_state or {},
        after_state=after_state or {},
    )
    session.add(event)
    await session.flush()
    return event
