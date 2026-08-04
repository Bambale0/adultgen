"""Local filesystem object storage adapter for development and tests."""

from __future__ import annotations

import asyncio
import shutil
from pathlib import Path


class LocalObjectStorage:
    """Filesystem-backed object storage.

    This adapter is intentionally simple and useful for CI/dev. Production can use
    an S3-compatible adapter behind the same ObjectStorage protocol.
    """

    def __init__(self, root: Path | str) -> None:
        self.root = Path(root)

    async def put_object(
        self,
        *,
        bucket: str,
        key: str,
        body: bytes,
        content_type: str,
    ) -> None:
        """Persist object bytes under bucket/key."""

        await asyncio.to_thread(self._write_bytes, bucket, key, body)

    async def copy_object(
        self,
        *,
        source_bucket: str,
        source_key: str,
        target_bucket: str,
        target_key: str,
        content_type: str,
    ) -> None:
        """Copy object bytes between local bucket/key paths."""

        await asyncio.to_thread(
            self._copy_file,
            source_bucket,
            source_key,
            target_bucket,
            target_key,
        )

    async def delete_object(self, *, bucket: str, key: str) -> None:
        """Delete an object if present."""

        await asyncio.to_thread(self._delete_file, bucket, key)

    def _write_bytes(self, bucket: str, key: str, body: bytes) -> None:
        target = self._path(bucket, key)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)

    def _copy_file(
        self,
        source_bucket: str,
        source_key: str,
        target_bucket: str,
        target_key: str,
    ) -> None:
        source = self._path(source_bucket, source_key)
        target = self._path(target_bucket, target_key)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)

    def _delete_file(self, bucket: str, key: str) -> None:
        self._path(bucket, key).unlink(missing_ok=True)

    def _path(self, bucket: str, key: str) -> Path:
        normalized_key = Path(key)
        if normalized_key.is_absolute() or ".." in normalized_key.parts:
            raise ValueError("Object storage key must be relative and safe.")
        return self.root / bucket / normalized_key
