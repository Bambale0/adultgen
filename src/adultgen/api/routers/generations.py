"""Generation task routes."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.api.dependencies import get_current_token_claims, get_db_session
from adultgen.api.schemas.generations import (
    CreateGenerationTaskRequest,
    GenerationListResponse,
    GenerationResultAssetResponse,
    GenerationTaskResponse,
)
from adultgen.db.models.generations import GenerationTask, SceneTake
from adultgen.db.models.media import MediaAsset
from adultgen.domain.model_capabilities import CapabilityValidationError
from adultgen.domain.pricing import PricingError
from adultgen.domain.wallet_ledger import WalletLedgerError
from adultgen.security.tokens import AccessTokenClaims
from adultgen.services.generations import GenerationServiceError, create_generation_task_with_reserve

router = APIRouter(prefix="/generations", tags=["generations"])


@router.post("", response_model=GenerationTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_generation_task(
    payload: CreateGenerationTaskRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    claims: Annotated[AccessTokenClaims, Depends(get_current_token_claims)],
) -> GenerationTaskResponse:
    """Create a generation task and reserve credits before provider submission."""

    try:
        task = await create_generation_task_with_reserve(
            session,
            user_id=claims.subject,
            model_code=payload.model_code,
            operation=payload.operation,
            request_payload=payload.request_payload,
            project_id=payload.project_id,
            scene_id=payload.scene_id,
        )
    except (CapabilityValidationError, PricingError, GenerationServiceError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    except WalletLedgerError as exc:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=str(exc)) from exc

    return await _task_response(session, task)


@router.get("", response_model=GenerationListResponse)
async def list_my_generation_tasks(
    claims: Annotated[AccessTokenClaims, Depends(get_current_token_claims)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
) -> GenerationListResponse:
    """List current user's recent generation tasks."""

    result = await session.execute(
        select(GenerationTask)
        .where(GenerationTask.user_id == claims.subject)
        .order_by(GenerationTask.created_at.desc())
        .limit(limit)
    )
    tasks = list(result.scalars())
    return GenerationListResponse(items=[await _task_response(session, task) for task in tasks])


@router.get("/{task_id}", response_model=GenerationTaskResponse)
async def get_generation_task_status(
    task_id: uuid.UUID,
    claims: Annotated[AccessTokenClaims, Depends(get_current_token_claims)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> GenerationTaskResponse:
    """Return one generation task with attached result media URLs."""

    result = await session.execute(
        select(GenerationTask).where(GenerationTask.id == task_id, GenerationTask.user_id == claims.subject)
    )
    task = result.scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Generation task not found.")
    return await _task_response(session, task)


async def _task_response(session: AsyncSession, task: GenerationTask) -> GenerationTaskResponse:
    return GenerationTaskResponse(
        id=task.id,
        status=task.status,
        provider=task.provider,
        model_code=task.model_code,
        operation=task.operation,
        reserved_credits=task.reserved_credits,
        charged_credits=task.charged_credits,
        provider_task_id=task.provider_task_id,
        error_code=task.error_code,
        error_message=task.error_message,
        results=await _result_assets(session, task.id),
    )


async def _result_assets(session: AsyncSession, task_id: uuid.UUID) -> list[GenerationResultAssetResponse]:
    take_result = await session.execute(select(SceneTake).where(SceneTake.generation_task_id == task_id))
    takes = list(take_result.scalars())
    result_asset_ids: list[tuple[str, uuid.UUID]] = []
    for take in takes:
        if take.video_asset_id:
            result_asset_ids.append(("video", take.video_asset_id))
        if take.image_asset_id:
            result_asset_ids.append(("image", take.image_asset_id))
        if take.last_frame_asset_id:
            result_asset_ids.append(("last_frame", take.last_frame_asset_id))
        if take.preview_asset_id:
            result_asset_ids.append(("preview", take.preview_asset_id))

    if not result_asset_ids:
        return []

    assets_result = await session.execute(
        select(MediaAsset).where(MediaAsset.id.in_([asset_id for _role, asset_id in result_asset_ids]))
    )
    assets_by_id = {asset.id: asset for asset in assets_result.scalars()}
    responses: list[GenerationResultAssetResponse] = []
    seen: set[tuple[str, uuid.UUID]] = set()
    for role, asset_id in result_asset_ids:
        key = (role, asset_id)
        if key in seen:
            continue
        seen.add(key)
        asset = assets_by_id.get(asset_id)
        if asset is None or asset.deleted_at is not None:
            continue
        responses.append(
            GenerationResultAssetResponse(
                asset_id=asset.id,
                role=role,
                media_url=f"/media/assets/{asset.id}/content",
                is_external=bool(asset.external_url),
            )
        )
    return responses
