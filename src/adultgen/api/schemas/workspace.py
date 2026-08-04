"""Workspace API schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class CreateAvatarProfileRequest(BaseModel):
    """Create avatar profile request."""

    name: str = Field(min_length=1, max_length=120)


class AvatarProfileResponse(BaseModel):
    """Avatar profile response."""

    id: uuid.UUID
    name: str
    status: str


class CreateProjectRequest(BaseModel):
    """Create project request."""

    title: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=2_000)
    output_format: str = Field(default="9:16", max_length=16)


class ProjectResponse(BaseModel):
    """Project response."""

    id: uuid.UUID
    title: str
    description: str | None
    status: str
    output_format: str


class CreateSceneRequest(BaseModel):
    """Create scene request."""

    prompt: str = Field(min_length=1, max_length=4_000)
    title: str | None = Field(default=None, max_length=160)
    duration_seconds: int = Field(default=5, ge=1, le=15)
    aspect_ratio: str = Field(default="9:16", max_length=16)
    camera_notes: str | None = Field(default=None, max_length=1_000)
    action_notes: str | None = Field(default=None, max_length=1_000)
    audio_notes: str | None = Field(default=None, max_length=1_000)


class SceneResponse(BaseModel):
    """Scene response."""

    id: uuid.UUID
    project_id: uuid.UUID
    order_index: int
    title: str | None
    prompt: str
    duration_seconds: int
    aspect_ratio: str
    status: str
