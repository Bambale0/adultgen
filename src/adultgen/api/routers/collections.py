"""Saved collection API routes."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.api.dependencies import get_current_token_claims, get_db_session
from adultgen.api.schemas.collections import (
    SavedPublicationListResponse,
    SavedPublicationResponse,
)
from adultgen.security.tokens import AccessTokenClaims
from adultgen.services.collections import (
    CollectionServiceError,
    list_saved_publications,
    save_publication,
    unsave_publication,
)

router = APIRouter(prefix="/collections", tags=["collections"])


@router.get("/saved", response_model=SavedPublicationListResponse)
async def list_my_saved_publications(
    claims: Annotated[AccessTokenClaims, Depends(get_current_token_claims)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> SavedPublicationListResponse:
    """List current user's saved publications."""

    try:
        saved_items = await list_saved_publications(session, user_id=claims.subject, limit=limit)
    except CollectionServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return SavedPublicationListResponse(
        items=[
            SavedPublicationResponse(
                publication_id=item.publication_id,
                saved_at=item.saved_at,
            )
            for item in saved_items
        ]
    )


@router.put("/saved/{publication_id}", response_model=SavedPublicationResponse)
async def save_my_publication(
    publication_id: uuid.UUID,
    claims: Annotated[AccessTokenClaims, Depends(get_current_token_claims)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SavedPublicationResponse:
    """Save publication to current user's collection."""

    try:
        saved = await save_publication(
            session,
            user_id=claims.subject,
            publication_id=publication_id,
        )
    except CollectionServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return SavedPublicationResponse(publication_id=saved.publication_id, saved_at=saved.saved_at)


@router.delete("/saved/{publication_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unsave_my_publication(
    publication_id: uuid.UUID,
    claims: Annotated[AccessTokenClaims, Depends(get_current_token_claims)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """Remove publication from current user's saved collection."""

    await unsave_publication(session, user_id=claims.subject, publication_id=publication_id)
