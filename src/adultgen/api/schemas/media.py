"""Media API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class MediaAssetResponse(BaseModel):
    """Media metadata returned after upload or lookup."""

    id: uuid.UUID
    storage_bucket: str
    storage_key: str
    media_type: str
    mime_type: str
    size_bytes: int | None
    checksum_sha256: str | None
    is_temporary: bool
    expires_at: datetime | None
    deleted_at: datetime | None


class MediaUploadResponse(BaseModel):
    """Upload response wrapper."""

    asset: MediaAssetResponse


class MediaDerivativeResponse(BaseModel):
    """Derivative metadata returned after preview/blur creation."""

    id: uuid.UUID
    source_asset_id: uuid.UUID
    derivative_asset_id: uuid.UUID
    variant: str
    status: str
    processor_version: str
    media_url: str
