"""Media derivative creation service."""

from __future__ import annotations

import uuid
from enum import StrEnum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.config import Settings
from adultgen.db.models.media import MediaAsset, MediaDerivative
from adultgen.storage.ports import ObjectStorage


class MediaDerivativeError(ValueError):
    """Raised when a media derivative cannot be created."""


class MediaDerivativeVariant(StrEnum):
    """Supported derivative variants for published media."""

    PREVIEW = "preview"
    BLUR = "blur"


async def ensure_media_derivative(
    session: AsyncSession,
    *,
    storage: ObjectStorage,
    settings: Settings,
    source_asset_id: uuid.UUID,
    variant: MediaDerivativeVariant,
) -> MediaDerivative:
    """Create or return a derivative asset for preview/blur rendering.

    MVP implementation copies the source bytes to a deterministic derivative key.
    The service boundary is intentionally stable so a future worker can replace the
    copy step with real image/video thumbnail and blur processing.
    """

    existing = await _get_existing_derivative(session, source_asset_id=source_asset_id, variant=variant)
    if existing is not None:
        return existing

    source = await _get_source_asset_for_update(session, source_asset_id)
    if source.deleted_at is not None:
        raise MediaDerivativeError("Deleted media asset cannot produce derivatives.")
    if source.storage_bucket != settings.s3_published_bucket:
        raise MediaDerivativeError("Only published media can produce public derivatives.")

    target_key = _derivative_key(source=source, variant=variant)
    await storage.copy_object(
        source_bucket=source.storage_bucket,
        source_key=source.storage_key,
        target_bucket=settings.s3_published_bucket,
        target_key=target_key,
        content_type=source.mime_type,
    )

    derivative_asset = MediaAsset(
        owner_user_id=source.owner_user_id,
        storage_bucket=settings.s3_published_bucket,
        storage_key=target_key,
        media_type=source.media_type,
        mime_type=source.mime_type,
        size_bytes=source.size_bytes,
        width=source.width,
        height=source.height,
        duration_seconds=source.duration_seconds,
        checksum_sha256=source.checksum_sha256,
        is_temporary=False,
        expires_at=None,
    )
    session.add(derivative_asset)
    await session.flush()

    derivative = MediaDerivative(
        source_asset_id=source.id,
        derivative_asset_id=derivative_asset.id,
        variant=variant.value,
        status="ready",
        processor_version="copy-placeholder-v1",
    )
    session.add(derivative)
    await session.flush()
    return derivative


async def get_media_derivative(
    session: AsyncSession,
    *,
    source_asset_id: uuid.UUID,
    variant: MediaDerivativeVariant,
) -> MediaDerivative | None:
    """Return an existing derivative by source asset and variant."""

    return await _get_existing_derivative(session, source_asset_id=source_asset_id, variant=variant)


async def list_media_derivatives(
    session: AsyncSession,
    *,
    source_asset_id: uuid.UUID,
) -> list[MediaDerivative]:
    """List derivatives for a source media asset."""

    result = await session.execute(
        select(MediaDerivative)
        .where(MediaDerivative.source_asset_id == source_asset_id)
        .order_by(MediaDerivative.variant)
    )
    return list(result.scalars())


async def _get_existing_derivative(
    session: AsyncSession,
    *,
    source_asset_id: uuid.UUID,
    variant: MediaDerivativeVariant,
) -> MediaDerivative | None:
    result = await session.execute(
        select(MediaDerivative).where(
            MediaDerivative.source_asset_id == source_asset_id,
            MediaDerivative.variant == variant.value,
        )
    )
    return result.scalar_one_or_none()


async def _get_source_asset_for_update(session: AsyncSession, source_asset_id: uuid.UUID) -> MediaAsset:
    result = await session.execute(
        select(MediaAsset).where(MediaAsset.id == source_asset_id).with_for_update()
    )
    source = result.scalar_one_or_none()
    if source is None:
        raise MediaDerivativeError("Source media asset not found.")
    return source


def _derivative_key(*, source: MediaAsset, variant: MediaDerivativeVariant) -> str:
    filename = source.storage_key.rsplit("/", maxsplit=1)[-1]
    return f"derivatives/{variant.value}/{source.id}/{filename}"
