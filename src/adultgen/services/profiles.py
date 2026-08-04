"""User profile application service."""

from __future__ import annotations

import secrets
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.db.models.publications import UserProfile


class ProfileServiceError(ValueError):
    """Raised when profile operation cannot be completed."""


PROFILE_PRIVATE = "private"
PROFILE_PUBLIC = "public"
_ALLOWED_VISIBILITIES = {PROFILE_PRIVATE, PROFILE_PUBLIC}


async def get_or_create_user_profile(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
) -> UserProfile:
    """Return user's profile, creating a private profile when missing."""

    result = await session.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if profile is not None:
        return profile

    profile = UserProfile(
        user_id=user_id,
        public_id=await _generate_unique_public_id(session),
        visibility=PROFILE_PRIVATE,
    )
    session.add(profile)
    await session.flush()
    return profile


async def update_user_profile(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    display_name: str | None = None,
    bio: str | None = None,
    visibility: str | None = None,
) -> UserProfile:
    """Update profile display fields and visibility."""

    profile = await get_or_create_user_profile(session, user_id=user_id)

    if display_name is not None:
        profile.display_name = display_name.strip() or None
    if bio is not None:
        profile.bio = bio.strip() or None
    if visibility is not None:
        if visibility not in _ALLOWED_VISIBILITIES:
            raise ProfileServiceError("Unsupported profile visibility.")
        profile.visibility = visibility

    await session.flush()
    return profile


async def get_public_profile_by_public_id(
    session: AsyncSession,
    *,
    public_id: str,
) -> UserProfile:
    """Return a public profile by public id."""

    result = await session.execute(
        select(UserProfile).where(
            UserProfile.public_id == public_id,
            UserProfile.visibility == PROFILE_PUBLIC,
        )
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise ProfileServiceError("Public profile not found.")
    return profile


async def _generate_unique_public_id(session: AsyncSession) -> str:
    for _attempt in range(10):
        public_id = secrets.token_urlsafe(8).replace("-", "_")[:11]
        result = await session.execute(
            select(UserProfile.id).where(UserProfile.public_id == public_id)
        )
        if result.scalar_one_or_none() is None:
            return public_id
    raise ProfileServiceError("Could not generate unique profile public id.")
