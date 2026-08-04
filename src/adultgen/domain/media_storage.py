"""Pure media storage helpers and policies."""

from __future__ import annotations

import hashlib
import mimetypes
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum


class MediaStorageError(ValueError):
    """Raised when media metadata cannot be planned safely."""


class MediaBucketRole(StrEnum):
    """Logical media bucket roles."""

    TEMPORARY = "temporary"
    PUBLISHED = "published"
    REFERENCES = "references"
    WEBHOOK_ARCHIVE = "webhook_archive"


class MediaType(StrEnum):
    """Supported first-class media types."""

    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class BucketNames:
    """Configured physical bucket names."""

    temporary: str
    published: str
    references: str
    webhook_archive: str


@dataclass(frozen=True, slots=True)
class PlannedMediaObject:
    """Storage destination planned before upload/metadata insert."""

    bucket: str
    key: str
    media_type: MediaType
    mime_type: str
    checksum_sha256: str
    size_bytes: int
    is_temporary: bool
    expires_at: datetime | None


def sha256_hex(raw: bytes) -> str:
    """Return SHA-256 digest for immutable media/audit references."""

    return hashlib.sha256(raw).hexdigest()


def infer_media_type(mime_type: str) -> MediaType:
    """Infer top-level AdultGen media type from MIME type."""

    if mime_type.startswith("image/"):
        return MediaType.IMAGE
    if mime_type.startswith("video/"):
        return MediaType.VIDEO
    if mime_type.startswith("audio/"):
        return MediaType.AUDIO
    return MediaType.OTHER


def guess_mime_type(filename: str | None, fallback: str = "application/octet-stream") -> str:
    """Guess MIME type from filename, with a safe fallback."""

    if not filename:
        return fallback
    guessed, _encoding = mimetypes.guess_type(filename)
    return guessed or fallback


def plan_media_object(
    *,
    owner_user_id: uuid.UUID | None,
    role: MediaBucketRole,
    buckets: BucketNames,
    raw: bytes,
    filename: str | None,
    mime_type: str | None = None,
    now: datetime | None = None,
    temporary_ttl: timedelta = timedelta(hours=24),
) -> PlannedMediaObject:
    """Plan object storage bucket/key/TTL for a media payload."""

    if not raw:
        raise MediaStorageError("Media payload cannot be empty.")
    if temporary_ttl.total_seconds() <= 0:
        raise MediaStorageError("Temporary media TTL must be positive.")

    resolved_now = now or datetime.now(UTC)
    resolved_mime_type = mime_type or guess_mime_type(filename)
    media_type = infer_media_type(resolved_mime_type)
    checksum = sha256_hex(raw)
    suffix = _safe_extension(filename, resolved_mime_type)
    key = _build_storage_key(
        owner_user_id=owner_user_id,
        role=role,
        checksum=checksum,
        suffix=suffix,
        now=resolved_now,
    )

    is_temporary = role == MediaBucketRole.TEMPORARY
    return PlannedMediaObject(
        bucket=_bucket_name(role, buckets),
        key=key,
        media_type=media_type,
        mime_type=resolved_mime_type,
        checksum_sha256=checksum,
        size_bytes=len(raw),
        is_temporary=is_temporary,
        expires_at=resolved_now + temporary_ttl if is_temporary else None,
    )


def _bucket_name(role: MediaBucketRole, buckets: BucketNames) -> str:
    match role:
        case MediaBucketRole.TEMPORARY:
            return buckets.temporary
        case MediaBucketRole.PUBLISHED:
            return buckets.published
        case MediaBucketRole.REFERENCES:
            return buckets.references
        case MediaBucketRole.WEBHOOK_ARCHIVE:
            return buckets.webhook_archive


def _build_storage_key(
    *,
    owner_user_id: uuid.UUID | None,
    role: MediaBucketRole,
    checksum: str,
    suffix: str,
    now: datetime,
) -> str:
    owner_part = str(owner_user_id) if owner_user_id else "system"
    date_part = now.strftime("%Y/%m/%d")
    object_id = uuid.uuid4().hex
    return f"{role.value}/{date_part}/{owner_part}/{checksum[:12]}-{object_id}{suffix}"


def _safe_extension(filename: str | None, mime_type: str) -> str:
    if filename and "." in filename:
        suffix = filename.rsplit(".", maxsplit=1)[-1].lower()
        if suffix and suffix.isalnum() and len(suffix) <= 8:
            return f".{suffix}"

    guessed = mimetypes.guess_extension(mime_type)
    return guessed or ""
