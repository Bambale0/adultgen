"""Adult consent application service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.db.models.users import AdultConsent


async def get_active_adult_consent(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    policy_version: str,
) -> AdultConsent | None:
    """Return active adult consent for the given policy version, if present."""

    result = await session.execute(
        select(AdultConsent)
        .where(
            AdultConsent.user_id == user_id,
            AdultConsent.policy_version == policy_version,
            AdultConsent.revoked_at.is_(None),
        )
        .order_by(AdultConsent.accepted_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def has_active_adult_consent(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    policy_version: str,
) -> bool:
    """Return whether user accepted the current adult policy."""

    return await get_active_adult_consent(
        session,
        user_id=user_id,
        policy_version=policy_version,
    ) is not None


async def accept_adult_consent(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    policy_version: str,
    source_channel_id: uuid.UUID | None = None,
    now: datetime | None = None,
) -> AdultConsent:
    """Record adult policy acceptance, reusing active acceptance when present."""

    existing = await get_active_adult_consent(
        session,
        user_id=user_id,
        policy_version=policy_version,
    )
    if existing is not None:
        return existing

    consent = AdultConsent(
        user_id=user_id,
        policy_version=policy_version,
        source_channel_id=source_channel_id,
        accepted_at=now or datetime.now(UTC),
    )
    session.add(consent)
    await session.flush()
    return consent
