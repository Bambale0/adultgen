"""Publication and feed application service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.config import Settings
from adultgen.db.models.media import MediaAsset
from adultgen.db.models.publications import Publication
from adultgen.domain.enums import PublicationStatus, PublicationVisibility
from adultgen.services.media import promote_media_asset_to_published
from adultgen.storage.ports import ObjectStorage


class PublicationServiceError(ValueError):
    """Raised when publication operations cannot be completed."""


async def create_publication(
    session: AsyncSession,
    *,
    storage: ObjectStorage,
    settings: Settings,
    user_id: uuid.UUID,
    asset_id: uuid.UUID,
    visibility: PublicationVisibility,
    title: str | None,
    description: str | None,
    project_id: uuid.UUID | None = None,
    scene_take_id: uuid.UUID | None = None,
    is_explicit: bool = True,
    blur_required: bool = True,
    allow_remix: bool = True,
    prompt_public: bool = False,
) -> Publication:
    """Publish an owned media asset into profile or common feed."""

    asset = await _get_owned_media_asset(session, user_id=user_id, asset_id=asset_id)
    if asset.deleted_at is not None:
        raise PublicationServiceError("Deleted media asset cannot be published.")

    await promote_media_asset_to_published(
        session,
        storage=storage,
        settings=settings,
        asset_id=asset.id,
    )

    publication = Publication(
        user_id=user_id,
        project_id=project_id,
        scene_take_id=scene_take_id,
        asset_id=asset.id,
        title=title,
        description=description,
        visibility=visibility.value,
        is_explicit=is_explicit,
        blur_required=blur_required or is_explicit,
        allow_remix=allow_remix,
        prompt_public=prompt_public,
        status=PublicationStatus.ACTIVE.value,
        published_at=datetime.now(UTC),
    )
    session.add(publication)
    await session.flush()
    return publication


async def list_feed_publications(
    session: AsyncSession,
    *,
    limit: int = 30,
) -> list[Publication]:
    """List active common-feed publications newest first."""

    if limit <= 0 or limit > 100:
        raise PublicationServiceError("Feed limit must be between 1 and 100.")

    result = await session.execute(
        select(Publication)
        .where(
            Publication.visibility == PublicationVisibility.FEED.value,
            Publication.status == PublicationStatus.ACTIVE.value,
            Publication.deleted_at.is_(None),
        )
        .order_by(Publication.published_at.desc())
        .limit(limit)
    )
    return list(result.scalars())


async def list_profile_publications(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    limit: int = 50,
) -> list[Publication]:
    """List active profile publications for the current user."""

    if limit <= 0 or limit > 100:
        raise PublicationServiceError("Profile publication limit must be between 1 and 100.")

    result = await session.execute(
        select(Publication)
        .where(
            Publication.user_id == user_id,
            Publication.status == PublicationStatus.ACTIVE.value,
            Publication.deleted_at.is_(None),
        )
        .order_by(Publication.published_at.desc())
        .limit(limit)
    )
    return list(result.scalars())


async def _get_owned_media_asset(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> MediaAsset:
    result = await session.execute(
        select(MediaAsset).where(
            MediaAsset.id == asset_id,
            MediaAsset.owner_user_id == user_id,
        )
    )
    asset = result.scalar_one_or_none()
    if asset is None:
        raise PublicationServiceError("Media asset not found for current user.")
    return asset
