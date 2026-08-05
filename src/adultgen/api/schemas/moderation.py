"""Moderation API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ModerationCaseResponse(BaseModel):
    """Moderation case exposed through API."""

    id: uuid.UUID
    publication_id: uuid.UUID | None
    reported_user_id: uuid.UUID | None
    reporter_user_id: uuid.UUID | None
    category: str
    description: str | None
    status: str
    priority: int
    resolution: str | None
    resolved_by_admin_id: uuid.UUID | None
    resolved_at: datetime | None
    created_at: datetime


class ModerationQueueResponse(BaseModel):
    """Admin moderation queue response."""

    items: list[ModerationCaseResponse]


class ReportPublicationRequest(BaseModel):
    """User report for a publication."""

    category: str = Field(min_length=2, max_length=80)
    description: str | None = Field(default=None, max_length=2_000)


class ResolveModerationCaseRequest(BaseModel):
    """Admin moderation resolution request."""

    action: str = Field(default="resolve", min_length=3, max_length=40)
    resolution: str = Field(min_length=2, max_length=2_000)
