"""User workspace creation service."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.db.models.projects import AvatarProfile, Project, Scene
from adultgen.domain.enums import ProjectStatus


class WorkspaceServiceError(ValueError):
    """Raised when workspace operation cannot be completed."""


async def create_avatar_profile(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    name: str,
) -> AvatarProfile:
    """Create a private avatar profile for a user."""

    avatar = AvatarProfile(
        user_id=user_id,
        name=name.strip(),
        status="active",
    )
    if not avatar.name:
        raise WorkspaceServiceError("Avatar name cannot be empty.")

    session.add(avatar)
    await session.flush()
    return avatar


async def create_project(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    title: str,
    description: str | None = None,
    output_format: str = "9:16",
) -> Project:
    """Create a user-owned generation project."""

    project = Project(
        user_id=user_id,
        title=title.strip(),
        description=description.strip() if description else None,
        status=ProjectStatus.DRAFT.value,
        output_format=output_format,
    )
    if not project.title:
        raise WorkspaceServiceError("Project title cannot be empty.")

    session.add(project)
    await session.flush()
    return project


async def create_scene(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    project_id: uuid.UUID,
    prompt: str,
    title: str | None = None,
    duration_seconds: int = 5,
    aspect_ratio: str = "9:16",
    camera_notes: str | None = None,
    action_notes: str | None = None,
    audio_notes: str | None = None,
) -> Scene:
    """Create next ordered scene in a user-owned project."""

    project = await _get_owned_project(session, user_id=user_id, project_id=project_id)
    order_index = await _next_scene_order_index(session, project_id=project.id)
    scene = Scene(
        project_id=project.id,
        order_index=order_index,
        title=title.strip() if title else None,
        prompt=prompt.strip(),
        duration_seconds=duration_seconds,
        aspect_ratio=aspect_ratio,
        camera_notes=camera_notes.strip() if camera_notes else None,
        action_notes=action_notes.strip() if action_notes else None,
        audio_notes=audio_notes.strip() if audio_notes else None,
        status=ProjectStatus.DRAFT.value,
    )
    if not scene.prompt:
        raise WorkspaceServiceError("Scene prompt cannot be empty.")
    if scene.duration_seconds <= 0:
        raise WorkspaceServiceError("Scene duration must be positive.")

    session.add(scene)
    await session.flush()
    return scene


async def _get_owned_project(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    project_id: uuid.UUID,
) -> Project:
    result = await session.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == user_id,
            Project.deleted_at.is_(None),
        )
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise WorkspaceServiceError("Project not found.")
    return project


async def _next_scene_order_index(session: AsyncSession, *, project_id: uuid.UUID) -> int:
    result = await session.execute(
        select(func.max(Scene.order_index)).where(Scene.project_id == project_id)
    )
    current_max = result.scalar_one_or_none()
    return int(current_max or 0) + 1
