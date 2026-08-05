"""Object storage dependency helpers for API routes."""

from functools import lru_cache
from pathlib import Path

from adultgen.storage.local import LocalObjectStorage
from adultgen.storage.ports import ObjectStorage


@lru_cache(maxsize=1)
def get_object_storage() -> ObjectStorage:
    """Return object storage adapter for API uploads.

    MVP uses local filesystem storage so development and CI work without external
    S3 credentials. Production can swap this provider for an S3-compatible adapter
    without changing media/publication routes.
    """

    return LocalObjectStorage(Path("/tmp/adultgen-media"))
