"""Publication and feed API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from adultgen.domain.enums import PublicationVisibility


class CreatePublicationRequest(BaseModel):
    """Request to publish a media asset into profile or common feed."""

    asset_id: uuid.UUID
    title: str | None = Field(default=None, max_length=140)
    description: str | None = Field(default=None, max_length=2_000)
    visibility: PublicationVisibility
    project_id: uuid.UUID | None = None
    scene_take_id: uuid.UUID | None = None
    is_explicit: bool = True
    blur_required: bool = True
    allow_remix: bool = True
    prompt_public: bool = False


class PublicationResponse(BaseModel):
    """Publication payload for profile/feed clients."""

    id: uuid.UUID
    user_id: uuid.UUID
    project_id: uuid.UUID | None
    scene_take_id: uuid.UUID | None
    asset_id: uuid.UUID
    title: str | None
    description: str | None
    visibility: str
    is_explicit: bool
    blur_required: bool
    allow_remix: bool
    prompt_public: bool
    status: str
    published_at: datetime


class FeedResponse(BaseModel):
    """Simple feed page response."""

    items: list[PublicationResponse]
