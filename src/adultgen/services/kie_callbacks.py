"""Kie callback ingestion service."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.config import Settings
from adultgen.db.models.generations import GenerationProviderCallbackRaw, GenerationTask, SceneTake
from adultgen.domain.enums import GenerationStatus, ModelProvider
from adultgen.services.generations import complete_generation_task, fail_generation_task_and_release
from adultgen.services.media import register_external_media_asset


class KieCallbackError(ValueError):
    """Raised when a Kie callback cannot be processed."""


@dataclass(frozen=True, slots=True)
class ParsedKieCallback:
    """Normalized Kie callback payload."""

    provider_task_id: str
    status: str
    result_urls: tuple[str, ...]
    last_frame_url: str | None
    error_code: str | None
    error_message: str | None
    raw_payload: dict[str, object]


@dataclass(frozen=True, slots=True)
class KieCallbackResult:
    """Processed callback result."""

    provider_task_id: str
    generation_task_id: uuid.UUID | None
    status: str
    changed_task: bool
    result_asset_ids: tuple[uuid.UUID, ...]
    scene_take_id: uuid.UUID | None


async def ingest_kie_callback(
    session: AsyncSession,
    *,
    settings: Settings,
    payload: dict[str, object],
) -> KieCallbackResult:
    """Record and process a Kie generation callback."""

    parsed = parse_kie_callback(payload)
    task = await _get_task_by_provider_task_id(session, parsed.provider_task_id)
    raw = GenerationProviderCallbackRaw(
        provider=ModelProvider.KIE.value,
        provider_task_id=parsed.provider_task_id,
        generation_task_id=task.id if task else None,
        status=parsed.status,
        raw_payload=parsed.raw_payload,
        result_payload={
            "result_urls": list(parsed.result_urls),
            "last_frame_url": parsed.last_frame_url,
        },
        error_code=parsed.error_code,
        error_message=parsed.error_message,
        processed_at=datetime.now(UTC),
    )
    session.add(raw)
    await session.flush()

    if task is None:
        return KieCallbackResult(
            provider_task_id=parsed.provider_task_id,
            generation_task_id=None,
            status="unknown_task",
            changed_task=False,
            result_asset_ids=(),
            scene_take_id=None,
        )

    current_status = GenerationStatus(task.status)
    if current_status in {GenerationStatus.COMPLETED, GenerationStatus.FAILED, GenerationStatus.CANCELLED}:
        return KieCallbackResult(
            provider_task_id=parsed.provider_task_id,
            generation_task_id=task.id,
            status=current_status.value,
            changed_task=False,
            result_asset_ids=(),
            scene_take_id=None,
        )

    if parsed.status in {"completed", "success", "succeeded"}:
        return await _handle_completed_callback(session, settings=settings, task=task, parsed=parsed)
    if parsed.status in {"failed", "error", "cancelled", "canceled"}:
        failed_task = await fail_generation_task_and_release(
            session,
            task_id=task.id,
            error_code=parsed.error_code or "provider_failed",
            error_message=parsed.error_message,
            technical_defect_detected=True,
        )
        return KieCallbackResult(
            provider_task_id=parsed.provider_task_id,
            generation_task_id=failed_task.id,
            status=failed_task.status,
            changed_task=True,
            result_asset_ids=(),
            scene_take_id=None,
        )

    task.status = GenerationStatus.PROVIDER_PROCESSING.value
    await session.flush()
    return KieCallbackResult(
        provider_task_id=parsed.provider_task_id,
        generation_task_id=task.id,
        status=task.status,
        changed_task=True,
        result_asset_ids=(),
        scene_take_id=None,
    )


def parse_kie_callback(payload: dict[str, object]) -> ParsedKieCallback:
    """Normalize provider-specific callback shape into AdultGen fields."""

    data = _as_mapping(payload.get("data"))
    provider_task_id = _first_string(
        payload.get("taskId"),
        payload.get("task_id"),
        payload.get("id"),
        data.get("taskId"),
        data.get("task_id"),
        data.get("id"),
    )
    if not provider_task_id:
        raise KieCallbackError("Kie callback is missing provider task id.")

    status = (
        _first_string(payload.get("status"), data.get("status"), payload.get("state"), data.get("state"))
        or "completed"
    )
    result_urls = tuple(_extract_result_urls(payload, data))
    last_frame_url = _first_string(
        payload.get("last_frame_url"),
        payload.get("lastFrameUrl"),
        data.get("last_frame_url"),
        data.get("lastFrameUrl"),
    )
    error_message = _first_string(
        payload.get("failed_reason"),
        payload.get("error"),
        payload.get("message"),
        data.get("failed_reason"),
        data.get("error"),
        data.get("message"),
    )
    error_code = _first_string(payload.get("error_code"), data.get("error_code"))

    return ParsedKieCallback(
        provider_task_id=provider_task_id,
        status=status.lower(),
        result_urls=result_urls,
        last_frame_url=last_frame_url,
        error_code=error_code,
        error_message=error_message,
        raw_payload=payload,
    )


async def _handle_completed_callback(
    session: AsyncSession,
    *,
    settings: Settings,
    task: GenerationTask,
    parsed: ParsedKieCallback,
) -> KieCallbackResult:
    result_asset_ids: list[uuid.UUID] = []
    for result_url in parsed.result_urls:
        asset = await register_external_media_asset(
            session,
            settings=settings,
            owner_user_id=task.user_id,
            external_url=result_url,
        )
        result_asset_ids.append(asset.id)

    last_frame_asset_id: uuid.UUID | None = None
    if parsed.last_frame_url:
        last_frame = await register_external_media_asset(
            session,
            settings=settings,
            owner_user_id=task.user_id,
            external_url=parsed.last_frame_url,
            filename="kie-last-frame.png",
            mime_type="image/png",
        )
        last_frame_asset_id = last_frame.id

    scene_take_id: uuid.UUID | None = None
    if task.scene_id and result_asset_ids:
        first_result_asset_id = result_asset_ids[0]
        take = SceneTake(
            generation_task_id=task.id,
            scene_id=task.scene_id,
            video_asset_id=first_result_asset_id if task.operation.startswith("video_") else None,
            image_asset_id=first_result_asset_id if task.operation.startswith("image_") else None,
            last_frame_asset_id=last_frame_asset_id,
            preview_asset_id=first_result_asset_id,
            is_approved=False,
        )
        session.add(take)
        await session.flush()
        scene_take_id = take.id

    completed_task = await complete_generation_task(session, task_id=task.id)
    return KieCallbackResult(
        provider_task_id=parsed.provider_task_id,
        generation_task_id=completed_task.id,
        status=completed_task.status,
        changed_task=True,
        result_asset_ids=tuple(result_asset_ids),
        scene_take_id=scene_take_id,
    )


async def _get_task_by_provider_task_id(session: AsyncSession, provider_task_id: str) -> GenerationTask | None:
    result = await session.execute(
        select(GenerationTask)
        .where(
            GenerationTask.provider == ModelProvider.KIE.value,
            GenerationTask.provider_task_id == provider_task_id,
        )
        .with_for_update()
    )
    return result.scalar_one_or_none()


def _extract_result_urls(payload: dict[str, object], data: dict[str, object]) -> list[str]:
    candidates: list[object] = [
        data.get("results"),
        data.get("result_urls"),
        data.get("resultUrls"),
        payload.get("results"),
        payload.get("result_urls"),
        payload.get("resultUrls"),
        data.get("video_url"),
        data.get("videoUrl"),
        data.get("image_url"),
        data.get("imageUrl"),
        payload.get("video_url"),
        payload.get("image_url"),
    ]
    urls: list[str] = []
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.startswith(("http://", "https://")):
            urls.append(candidate)
        elif isinstance(candidate, list):
            urls.extend(item for item in candidate if isinstance(item, str) and item.startswith(("http://", "https://")))
    return urls


def _as_mapping(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _first_string(*values: object) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None
