"""Profile API schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class UserProfileResponse(BaseModel):
    """User profile response."""

    id: uuid.UUID
    public_id: str
    display_name: str | None
    bio: str | None
    visibility: str


class UpdateUserProfileRequest(BaseModel):
    """Profile update request."""

    display_name: str | None = Field(default=None, max_length=120)
    bio: str | None = Field(default=None, max_length=500)
    visibility: str | None = Field(default=None, pattern="^(public|private)$")
