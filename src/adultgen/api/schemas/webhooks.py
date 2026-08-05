"""Webhook API schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel


class KieCallbackResponse(BaseModel):
    """Response returned after Kie callback ingestion."""

    provider_task_id: str
    generation_task_id: uuid.UUID | None
    status: str
    changed_task: bool
    result_asset_ids: list[uuid.UUID]
    scene_take_id: uuid.UUID | None = None
