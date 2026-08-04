from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from adultgen.domain.media_storage import (
    BucketNames,
    MediaBucketRole,
    MediaStorageError,
    MediaType,
    guess_mime_type,
    plan_media_object,
    sha256_hex,
)
from adultgen.storage.local import LocalObjectStorage


BUCKETS = BucketNames(
    temporary="media-temporary",
    published="media-published",
    references="media-references",
    webhook_archive="webhook-archive",
)


def test_plan_temporary_media_object_sets_bucket_checksum_and_expiration() -> None:
    raw = b"fake image bytes"
    now = datetime(2026, 8, 5, 0, 0, tzinfo=UTC)
    owner_user_id = uuid4()

    planned = plan_media_object(
        owner_user_id=owner_user_id,
        role=MediaBucketRole.TEMPORARY,
        buckets=BUCKETS,
        raw=raw,
        filename="photo.png",
        now=now,
        temporary_ttl=timedelta(hours=24),
    )

    assert planned.bucket == "media-temporary"
    assert planned.media_type == MediaType.IMAGE
    assert planned.mime_type == "image/png"
    assert planned.checksum_sha256 == sha256_hex(raw)
    assert planned.size_bytes == len(raw)
    assert planned.is_temporary is True
    assert planned.expires_at == now + timedelta(hours=24)
    assert planned.key.startswith(f"temporary/2026/08/05/{owner_user_id}/")
    assert planned.key.endswith(".png")


def test_plan_published_media_has_no_expiration() -> None:
    planned = plan_media_object(
        owner_user_id=None,
        role=MediaBucketRole.PUBLISHED,
        buckets=BUCKETS,
        raw=b"video",
        filename="clip.mp4",
        now=datetime(2026, 8, 5, 0, 0, tzinfo=UTC),
    )

    assert planned.bucket == "media-published"
    assert planned.media_type == MediaType.VIDEO
    assert planned.is_temporary is False
    assert planned.expires_at is None


def test_plan_media_rejects_empty_payload() -> None:
    with pytest.raises(MediaStorageError, match="cannot be empty"):
        plan_media_object(
            owner_user_id=None,
            role=MediaBucketRole.TEMPORARY,
            buckets=BUCKETS,
            raw=b"",
            filename="empty.png",
        )


def test_guess_mime_type_uses_safe_fallback() -> None:
    assert guess_mime_type("photo.jpg") == "image/jpeg"
    assert guess_mime_type("unknown.unknownext") == "application/octet-stream"


@pytest.mark.asyncio
async def test_local_object_storage_put_copy_delete(tmp_path: Path) -> None:
    storage = LocalObjectStorage(tmp_path)

    await storage.put_object(
        bucket="source",
        key="a/b/file.txt",
        body=b"hello",
        content_type="text/plain",
    )
    assert (tmp_path / "source" / "a" / "b" / "file.txt").read_bytes() == b"hello"

    await storage.copy_object(
        source_bucket="source",
        source_key="a/b/file.txt",
        target_bucket="target",
        target_key="copied.txt",
        content_type="text/plain",
    )
    assert (tmp_path / "target" / "copied.txt").read_bytes() == b"hello"

    await storage.delete_object(bucket="source", key="a/b/file.txt")
    assert not (tmp_path / "source" / "a" / "b" / "file.txt").exists()


@pytest.mark.asyncio
async def test_local_object_storage_rejects_unsafe_key(tmp_path: Path) -> None:
    storage = LocalObjectStorage(tmp_path)

    with pytest.raises(ValueError, match="relative and safe"):
        await storage.put_object(
            bucket="bucket",
            key="../escape.txt",
            body=b"bad",
            content_type="text/plain",
        )
