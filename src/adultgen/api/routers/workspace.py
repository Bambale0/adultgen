"""Workspace API routes."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.api.dependencies import get_current_token_claims, get_db_session
from adultgen.api.schemas.workspace import (
    AvatarProfileResponse,
    CreateAvatarProfileRequest,
    CreateProjectRequest,
    CreateSceneRequest,
    ProjectResponse,
    SceneResponse,
)
from adultgen.security.tokens import AccessTokenClaims
from adultgen.services.workspace import (
    WorkspaceServiceError,
    create_avatar_profile,
    create_project,
    create_scene,
)

router = APIRouter(prefix="/workspace", tags=["workspace"])


@router.post("/avatars", response_model=AvatarProfileResponse)
async def create_avatar(
    payload: CreateAvatarProfileRequest,
    claims: Annotated[AccessTokenClaims, Depends(get_current_token_claims)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AvatarProfileResponse:
    """Create a private avatar profile."""

    try:
        avatar = await create_avatar_profile(session, user_id=claims.subject, name=payload.name)
    except WorkspaceServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return AvatarProfileResponse(id=avatar.id, name=avatar.name, status=avatar.status)


@router.post("/projects", response_model=ProjectResponse)
async def create_workspace_project(
    payload: CreateProjectRequest,
    claims: Annotated[AccessTokenClaims, Depends(get_current_token_claims)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ProjectResponse:
    """Create a user-owned generation project."""

    try:
        project = await create_project(
            session,
            user_id=claims.subject,
            title=payload.title,
            description=payload.description,
            output_format=payload.output_format,
        )
    except WorkspaceServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return ProjectResponse(
        id=project.id,
        title=project.title,
        description=project.description,
        status=project.status,
        output_format=project.output_format,
    )


@router.post("/projects/{project_id}/scenes", response_model=SceneResponse)
async def create_project_scene(
    project_id: uuid.UUID,
    payload: CreateSceneRequest,
    claims: Annotated[AccessTokenClaims, Depends(get_current_token_claims)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SceneResponse:
    """Create a scene inside an owned project."""

    try:
        scene = await create_scene(
            session,
            user_id=claims.subject,
            project_id=project_id,
            prompt=payload.prompt,
            title=payload.title,
            duration_seconds=payload.duration_seconds,
            aspect_ratio=payload.aspect_ratio,
            camera_notes=payload.camera_notes,
            action_notes=payload.action_notes,
            audio_notes=payload.audio_notes,
        )
    except WorkspaceServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return SceneResponse(
        id=scene.id,
        project_id=scene.project_id,
        order_index=scene.order_index,
        title=scene.title,
        prompt=scene.prompt,
        duration_seconds=scene.duration_seconds,
        aspect_ratio=scene.aspect_ratio,
        status=scene.status,
    )
