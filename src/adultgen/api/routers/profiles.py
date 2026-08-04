"""Profile API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.api.dependencies import get_current_token_claims, get_db_session
from adultgen.api.schemas.profiles import UpdateUserProfileRequest, UserProfileResponse
from adultgen.security.tokens import AccessTokenClaims
from adultgen.services.profiles import (
    ProfileServiceError,
    get_or_create_user_profile,
    get_public_profile_by_public_id,
    update_user_profile,
)

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    claims: Annotated[AccessTokenClaims, Depends(get_current_token_claims)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserProfileResponse:
    """Return current user's profile, creating a private one if missing."""

    profile = await get_or_create_user_profile(session, user_id=claims.subject)
    return _profile_response(profile)


@router.patch("/me", response_model=UserProfileResponse)
async def patch_my_profile(
    payload: UpdateUserProfileRequest,
    claims: Annotated[AccessTokenClaims, Depends(get_current_token_claims)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserProfileResponse:
    """Update current user's public/private profile settings."""

    try:
        profile = await update_user_profile(
            session,
            user_id=claims.subject,
            display_name=payload.display_name,
            bio=payload.bio,
            visibility=payload.visibility,
        )
    except ProfileServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _profile_response(profile)


@router.get("/{public_id}", response_model=UserProfileResponse)
async def get_public_profile(
    public_id: str,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserProfileResponse:
    """Return public profile by public id."""

    try:
        profile = await get_public_profile_by_public_id(session, public_id=public_id)
    except ProfileServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _profile_response(profile)


def _profile_response(profile) -> UserProfileResponse:
    return UserProfileResponse(
        id=profile.id,
        public_id=profile.public_id,
        display_name=profile.display_name,
        bio=profile.bio,
        visibility=profile.visibility,
    )
