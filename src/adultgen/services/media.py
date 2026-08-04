"""Media asset application service."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.config import Settings
from adultgen.db.models.media import MediaAsset
from adultgen.domain.media_storage import (
    BucketNames,
    MediaBucketRole,
    MediaStorageError,
    plan_media_object,
)
from adultgen.storage.ports import ObjectStorage


class MediaServiceError(ValueError):
    """Raised when media service cannot complete an operation."""


@dataclass(frozen=True, slots=True)
class UploadMediaCommand:
    """Command for upload + metadata registration."""

    owner_user_id: uuid.UUID | None
    raw: bytes
    filename: str | None
    mime_type: str | None = None
    role: MediaBucketRole = MediaBucketRole.TEMPORARY
    telegram_file_id: str | None = None


async def upload_media_asset(
    session: AsyncSession,
    *,
    storage: ObjectStorage,
    settings: Settings,
    command: UploadMediaCommand,
    now: datetime | None = None,
) -> MediaAsset:
    """Upload media bytes and create MediaAsset metadata."""

    planned = plan_media_object(
        owner_user_id=command.owner_user_id,
        role=command.role,
        buckets=_bucket_names(settings),
        raw=command.raw,
        filename=command.filename,
        mime_type=command.mime_type,
        now=now,
        temporary_ttl=timedelta(seconds=settings.media_temp_ttl_seconds),
    )
    await storage.put_object(
        bucket=planned.bucket,
        key=planned.key,
        body=command.raw,
        content_type=planned.mime_type,
    )

    asset = MediaAsset(
        owner_user_id=command.owner_user_id,
        storage_bucket=planned.bucket,
        storage_key=planned.key,
        media_type=planned.media_type.value,
        mime_type=planned.mime_type,
        size_bytes=planned.size_bytes,
        checksum_sha256=planned.checksum_sha256,
        telegram_file_id=command.telegram_file_id,
        is_temporary=planned.is_temporary,
        expires_at=planned.expires_at,
    )
    session.add(asset)
    await session.flush()
    return asset


async def promote_media_asset_to_published(
    session: AsyncSession,
    *,
    storage: ObjectStorage,
    settings: Settings,
    asset_id: uuid.UUID,
    now: datetime | None = None,
) -> MediaAsset:
    """Copy a temporary/reference media asset into the published bucket."""

    asset = await _get_media_asset_for_update(session, asset_id)
    if asset.deleted_at is not None:
        raise MediaServiceError("Deleted media asset cannot be promoted.")
    if asset.storage_bucket == settings.s3_published_bucket and not asset.is_temporary:
        return asset

    target_key = asset.storage_key.replace("temporary/", "published/", 1)
    if target_key == asset.storage_key:
        target_key = f"published/{asset.id}/{asset.storage_key.rsplit('/', maxsplit=1)[-1]}"

    await storage.copy_object(
        source_bucket=asset.storage_bucket,
        source_key=asset.storage_key,
        target_bucket=settings.s3_published_bucket,
        target_key=target_key,
        content_type=asset.mime_type,
    )

    asset.storage_bucket = settings.s3_published_bucket
    asset.storage_key = target_key
    asset.is_temporary = False
    asset.expires_at = None
    await session.flush()
    return asset


async def mark_media_asset_deleted(
    session: AsyncSession,
    *,
    storage: ObjectStorage,
    asset_id: uuid.UUID,
    now: datetime | None = None,
) -> MediaAsset:
    """Soft-delete metadata and delete the backing object."""

    asset = await _get_media_asset_for_update(session, asset_id)
    if asset.deleted_at is not None:
        return asset

    await storage.delete_object(bucket=asset.storage_bucket, key=asset.storage_key)
    asset.deleted_at = now or datetime.now(UTC)
    await session.flush()
    return asset


async def list_expired_temporary_media(
    session: AsyncSession,
    *,
    now: datetime | None = None,
    limit: int = 100,
) -> list[MediaAsset]:
    """Return expired temporary media candidates for cleanup workers."""

    if limit <= 0:
        raise MediaStorageError("Expired media cleanup limit must be positive.")

    resolved_now = now or datetime.now(UTC)
    result = await session.execute(
        select(MediaAsset)
        .where(
            MediaAsset.is_temporary.is_(True),
            MediaAsset.expires_at.is_not(None),
            MediaAsset.expires_at <= resolved_now,
            MediaAsset.deleted_at.is_(None),
        )
        .order_by(MediaAsset.expires_at)
        .limit(limit)
    )
    return list(result.scalars())


async def _get_media_asset_for_update(session: AsyncSession, asset_id: uuid.UUID) -> MediaAsset:
    result = await session.execute(
        select(MediaAsset).where(MediaAsset.id == asset_id).with_for_update()
    )
    asset = result.scalar_one_or_none()
    if asset is None:
        raise MediaServiceError("Media asset not found.")
    return asset


def _bucket_names(settings: Settings) -> BucketNames:
    return BucketNames(
        temporary=settings.s3_temp_bucket,
        published=settings.s3_published_bucket,
        references=settings.s3_references_bucket,
        webhook_archive=settings.s3_webhook_bucket,
    )
