"""Object storage dependency helpers for API routes."""

from functools import lru_cache
from pathlib import Path

from adultgen.config import get_settings
from adultgen.storage.local import LocalObjectStorage
from adultgen.storage.ports import ObjectStorage
from adultgen.storage.s3 import S3ObjectStorage, S3ObjectStorageConfig


@lru_cache(maxsize=1)
def get_object_storage() -> ObjectStorage:
    """Return configured object storage adapter."""

    settings = get_settings()
    backend = settings.object_storage_backend.lower()
    if backend == "local":
        return LocalObjectStorage(Path("/tmp/adultgen-media"))
    if backend == "s3":
        return S3ObjectStorage(
            S3ObjectStorageConfig(
                endpoint_url=settings.s3_endpoint_url,
                access_key=settings.s3_access_key,
                secret_key=settings.s3_secret_key,
                region_name=settings.s3_region_name,
            )
        )
    raise RuntimeError(f"Unsupported object storage backend: {settings.object_storage_backend}")
