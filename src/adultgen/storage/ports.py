"""Object storage protocol used by media services."""

from __future__ import annotations

from typing import Protocol


class ObjectStorage(Protocol):
    """Minimal async object storage interface."""

    async def put_object(
        self,
        *,
        bucket: str,
        key: str,
        body: bytes,
        content_type: str,
    ) -> None:
        """Persist an object."""

    async def copy_object(
        self,
        *,
        source_bucket: str,
        source_key: str,
        target_bucket: str,
        target_key: str,
        content_type: str,
    ) -> None:
        """Copy an object between buckets/keys."""

    async def delete_object(self, *, bucket: str, key: str) -> None:
        """Delete an object if it exists."""
