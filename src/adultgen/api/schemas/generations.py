"""Generation API schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, Field

from adultgen.domain.enums import GenerationOperation, ModelCode


class CreateGenerationTaskRequest(BaseModel):
    """Mini App request to create and reserve a generation task."""

    model_code: ModelCode
    operation: GenerationOperation
    request_payload: dict[str, object] = Field(default_factory=dict)
    project_id: uuid.UUID | None = None
    scene_id: uuid.UUID | None = None


class GenerationResultAssetResponse(BaseModel):
    """A media result attached to a generation task."""

    asset_id: uuid.UUID
    role: str
    media_url: str
    is_external: bool


class GenerationTaskResponse(BaseModel):
    """Generation task state returned to API clients."""

    id: uuid.UUID
    status: str
    provider: str
    model_code: str
    operation: str
    reserved_credits: int
    charged_credits: int
    provider_task_id: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    results: list[GenerationResultAssetResponse] = Field(default_factory=list)


class GenerationListResponse(BaseModel):
    """Current user's generation task list."""

    items: list[GenerationTaskResponse]
