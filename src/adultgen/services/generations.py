"""Generation task lifecycle service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.db.models.generations import GenerationTask
from adultgen.domain.enums import GenerationOperation, GenerationStatus, ModelCode, ModelProvider
from adultgen.domain.model_capabilities import validate_generation_payload
from adultgen.domain.pricing import calculate_generation_price
from adultgen.services.wallets import charge_reserved_credits, release_reserved_credits, reserve_credits


class GenerationServiceError(ValueError):
    """Raised when generation lifecycle cannot be advanced safely."""


async def create_generation_task_with_reserve(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    model_code: ModelCode,
    operation: GenerationOperation,
    request_payload: dict[str, object],
    project_id: uuid.UUID | None = None,
    scene_id: uuid.UUID | None = None,
) -> GenerationTask:
    """Validate request, reserve credits, and create a queued generation task."""

    validate_generation_payload(model_code, operation, request_payload)
    price = calculate_generation_price(model_code, operation, request_payload)
    if price <= 0:
        raise GenerationServiceError("Generation price must be positive.")

    task = GenerationTask(
        user_id=user_id,
        project_id=project_id,
        scene_id=scene_id,
        provider=ModelProvider.KIE.value,
        model_code=model_code.value,
        operation=operation.value,
        status=GenerationStatus.CREATED.value,
        request_payload=request_payload,
        reserved_credits=price,
        charged_credits=0,
    )
    session.add(task)
    await session.flush()

    await reserve_credits(
        session,
        user_id=user_id,
        amount=price,
        operation_id=task.id,
        generation_task_id=task.id,
        reason="generation_task_created",
    )

    task.status = GenerationStatus.QUEUED.value
    await session.flush()
    return task


async def mark_generation_submitted(
    session: AsyncSession,
    *,
    task_id: uuid.UUID,
    provider_task_id: str,
) -> GenerationTask:
    """Mark a queued task as submitted to the provider."""

    task = await get_generation_task_for_update(session, task_id=task_id)
    _require_status(task, {GenerationStatus.QUEUED})

    task.provider_task_id = provider_task_id
    task.status = GenerationStatus.SUBMITTED.value
    task.submitted_at = datetime.now(tz=UTC)
    await session.flush()
    return task


async def mark_generation_provider_processing(
    session: AsyncSession,
    *,
    task_id: uuid.UUID,
) -> GenerationTask:
    """Mark a submitted task as processing on the provider side."""

    task = await get_generation_task_for_update(session, task_id=task_id)
    _require_status(task, {GenerationStatus.SUBMITTED})

    task.status = GenerationStatus.PROVIDER_PROCESSING.value
    await session.flush()
    return task


async def complete_generation_task(
    session: AsyncSession,
    *,
    task_id: uuid.UUID,
) -> GenerationTask:
    """Finalize a successful task and charge reserved credits."""

    task = await get_generation_task_for_update(session, task_id=task_id)
    _require_status(task, {GenerationStatus.SUBMITTED, GenerationStatus.PROVIDER_PROCESSING})

    await charge_reserved_credits(
        session,
        user_id=task.user_id,
        amount=task.reserved_credits,
        operation_id=task.id,
        generation_task_id=task.id,
        reason="generation_task_completed",
    )

    task.charged_credits = task.reserved_credits
    task.status = GenerationStatus.COMPLETED.value
    task.completed_at = datetime.now(tz=UTC)
    await session.flush()
    return task


async def fail_generation_task_and_release(
    session: AsyncSession,
    *,
    task_id: uuid.UUID,
    error_code: str,
    error_message: str | None = None,
    technical_defect_detected: bool = False,
) -> GenerationTask:
    """Fail a task and release all reserved credits back to the wallet."""

    task = await get_generation_task_for_update(session, task_id=task_id)
    _require_status(
        task,
        {
            GenerationStatus.CREATED,
            GenerationStatus.QUEUED,
            GenerationStatus.SUBMITTED,
            GenerationStatus.PROVIDER_PROCESSING,
        },
    )

    if task.reserved_credits > task.charged_credits:
        await release_reserved_credits(
            session,
            user_id=task.user_id,
            amount=task.reserved_credits - task.charged_credits,
            operation_id=task.id,
            generation_task_id=task.id,
            reason="generation_task_failed",
        )

    task.status = GenerationStatus.FAILED.value
    task.error_code = error_code
    task.error_message = error_message
    task.technical_defect_detected = technical_defect_detected
    task.completed_at = datetime.now(tz=UTC)
    await session.flush()
    return task


async def cancel_generation_task_and_release(
    session: AsyncSession,
    *,
    task_id: uuid.UUID,
) -> GenerationTask:
    """Cancel a task before completion and release reserved credits."""

    task = await get_generation_task_for_update(session, task_id=task_id)
    _require_status(task, {GenerationStatus.CREATED, GenerationStatus.QUEUED})

    if task.reserved_credits > 0:
        await release_reserved_credits(
            session,
            user_id=task.user_id,
            amount=task.reserved_credits,
            operation_id=task.id,
            generation_task_id=task.id,
            reason="generation_task_cancelled",
        )

    task.status = GenerationStatus.CANCELLED.value
    task.completed_at = datetime.now(tz=UTC)
    await session.flush()
    return task


async def get_generation_task_for_update(
    session: AsyncSession,
    *,
    task_id: uuid.UUID,
) -> GenerationTask:
    """Return a locked generation task."""

    result = await session.execute(select(GenerationTask).where(GenerationTask.id == task_id).with_for_update())
    task = result.scalar_one_or_none()
    if task is None:
        raise GenerationServiceError(f"Generation task {task_id} not found.")
    return task


def _require_status(task: GenerationTask, allowed_statuses: set[GenerationStatus]) -> None:
    current = GenerationStatus(task.status)
    if current not in allowed_statuses:
        allowed = ", ".join(sorted(status.value for status in allowed_statuses))
        raise GenerationServiceError(
            f"Generation task {task.id} status {current.value!r} cannot transition here; allowed: {allowed}."
        )
