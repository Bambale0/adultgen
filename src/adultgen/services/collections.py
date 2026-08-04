"""Saved publication collection service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.db.models.publications import Publication, SavedPublication
from adultgen.domain.enums import PublicationStatus


class CollectionServiceError(ValueError):
    """Raised when collection operation cannot be completed."""


async def save_publication(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    publication_id: uuid.UUID,
    now: datetime | None = None,
) -> SavedPublication:
    """Save an active publication into user's collection."""

    await _ensure_publication_can_be_saved(session, publication_id=publication_id)
    saved_at = now or datetime.now(UTC)
    await session.execute(
        insert(SavedPublication)
        .values(user_id=user_id, publication_id=publication_id, saved_at=saved_at)
        .on_conflict_do_nothing(index_elements=[SavedPublication.user_id, SavedPublication.publication_id])
    )
    result = await session.execute(
        select(SavedPublication).where(
            SavedPublication.user_id == user_id,
            SavedPublication.publication_id == publication_id,
        )
    )
    saved = result.scalar_one()
    return saved


async def unsave_publication(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    publication_id: uuid.UUID,
) -> None:
    """Remove saved publication from user's collection."""

    await session.execute(
        delete(SavedPublication).where(
            SavedPublication.user_id == user_id,
            SavedPublication.publication_id == publication_id,
        )
    )
    await session.flush()


async def list_saved_publications(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    limit: int = 50,
) -> list[SavedPublication]:
    """List saved publications for a user, newest first."""

    if limit <= 0 or limit > 100:
        raise CollectionServiceError("Saved collection limit must be between 1 and 100.")

    result = await session.execute(
        select(SavedPublication)
        .join(Publication, SavedPublication.publication_id == Publication.id)
        .where(
            SavedPublication.user_id == user_id,
            Publication.status == PublicationStatus.ACTIVE.value,
            Publication.deleted_at.is_(None),
        )
        .order_by(SavedPublication.saved_at.desc())
        .limit(limit)
    )
    return list(result.scalars())


async def _ensure_publication_can_be_saved(
    session: AsyncSession,
    *,
    publication_id: uuid.UUID,
) -> None:
    result = await session.execute(
        select(Publication.id).where(
            Publication.id == publication_id,
            Publication.status == PublicationStatus.ACTIVE.value,
            Publication.deleted_at.is_(None),
        )
    )
    if result.scalar_one_or_none() is None:
        raise CollectionServiceError("Publication is not available for saving.")
