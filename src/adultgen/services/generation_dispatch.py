"""Generation provider dispatch service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.db.models.generations import GenerationTask
from adultgen.domain.enums import GenerationOperation, GenerationStatus, ModelCode
from adultgen.domain.kie_payloads import build_kie_create_task_payload
from adultgen.integrations.kie.client import KieClient
from adultgen.services.generations import GenerationServiceError, get_generation_task_for_update


async def submit_queued_generation_to_kie(
    session: AsyncSession,
    *,
    task_id: uuid.UUID,
    kie_client: KieClient,
    callback_url: str,
) -> GenerationTask:
    """Submit a queued generation task to Kie and persist provider task id."""

    task = await get_generation_task_for_update(session, task_id=task_id)
    if GenerationStatus(task.status) != GenerationStatus.QUEUED:
        raise GenerationServiceError(
            f"Generation task {task.id} must be queued before provider submission; current={task.status!r}."
        )

    payload = build_kie_create_task_payload(
        model_code=ModelCode(task.model_code),
        operation=GenerationOperation(task.operation),
        request_payload=task.request_payload,
        callback_url=callback_url,
    )
    result = await kie_client.create_task(payload)

    task.provider_task_id = result.provider_task_id
    task.status = GenerationStatus.SUBMITTED.value
    task.submitted_at = datetime.now(tz=UTC)
    await session.flush()
    return task
