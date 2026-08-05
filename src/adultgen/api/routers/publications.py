"""Publication and feed API routes."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.api.dependencies import get_current_token_claims, get_db_session, get_runtime_settings
from adultgen.api.schemas.publications import CreatePublicationRequest, FeedResponse, PublicationResponse
from adultgen.api.storage import get_object_storage
from adultgen.config import Settings
from adultgen.db.models.media import MediaDerivative
from adultgen.db.models.publications import Publication
from adultgen.domain.adult_policy import AdultPolicyAction, evaluate_request_payload
from adultgen.domain.enums import PublicationVisibility
from adultgen.security.tokens import AccessTokenClaims
from adultgen.services.media_derivatives import MediaDerivativeVariant
from adultgen.services.moderation import create_policy_moderation_case
from adultgen.services.publications import (
    PublicationServiceError,
    create_publication,
    list_feed_publications,
    list_profile_publications,
)
from adultgen.storage.ports import ObjectStorage

router = APIRouter(tags=["publications"])


@router.post("/publications", response_model=PublicationResponse)
async def publish_media(
    payload: CreatePublicationRequest,
    claims: Annotated[AccessTokenClaims, Depends(get_current_token_claims)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_runtime_settings)],
    storage: Annotated[ObjectStorage, Depends(get_object_storage)],
) -> PublicationResponse:
    """Publish owned media into profile or common feed."""

    policy_decision = evaluate_request_payload(
        {
            "title": payload.title or "",
            "description": payload.description or "",
        },
        surface="publication_submit",
        is_public=payload.visibility == PublicationVisibility.FEED,
    )
    if policy_decision.action == AdultPolicyAction.BLOCK:
        await create_policy_moderation_case(
            session,
            user_id=claims.subject,
            decision=policy_decision,
            surface="publication_submit",
        )
        await session.commit()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Publication violates adult content policy.",
        )

    blur_required = payload.blur_required or payload.is_explicit or policy_decision.needs_review
    try:
        publication = await create_publication(
            session,
            storage=storage,
            settings=settings,
            user_id=claims.subject,
            asset_id=payload.asset_id,
            visibility=payload.visibility,
            title=payload.title,
            description=payload.description,
            project_id=payload.project_id,
            scene_take_id=payload.scene_take_id,
            is_explicit=payload.is_explicit,
            blur_required=blur_required,
            allow_remix=payload.allow_remix,
            prompt_public=payload.prompt_public,
        )
    except PublicationServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    if policy_decision.needs_review:
        await create_policy_moderation_case(
            session,
            user_id=claims.subject,
            decision=policy_decision,
            surface="publication_submit",
            publication_id=publication.id,
        )

    return await _publication_response(session, publication)


@router.get("/feed", response_model=FeedResponse)
async def list_common_feed(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
) -> FeedResponse:
    """List active common-feed publications."""

    try:
        publications = await list_feed_publications(session, limit=limit)
    except PublicationServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return FeedResponse(
        items=[await _publication_response(session, publication) for publication in publications]
    )


@router.get("/profiles/me/publications", response_model=FeedResponse)
async def list_my_profile_publications(
    claims: Annotated[AccessTokenClaims, Depends(get_current_token_claims)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> FeedResponse:
    """List current user's profile/feed publications."""

    try:
        publications = await list_profile_publications(session, user_id=claims.subject, limit=limit)
    except PublicationServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return FeedResponse(
        items=[await _publication_response(session, publication) for publication in publications]
    )


async def _publication_response(session: AsyncSession, publication: Publication) -> PublicationResponse:
    media_url = f"/media/assets/{publication.asset_id}/content"
    derivative_urls = await _publication_derivative_urls(session, publication.asset_id)
    preview_url = derivative_urls.get(MediaDerivativeVariant.PREVIEW.value) or f"{media_url}?variant=preview"
    blur_preview_url = None
    if publication.blur_required:
        blur_preview_url = derivative_urls.get(MediaDerivativeVariant.BLUR.value) or f"{media_url}?variant=blur"

    return PublicationResponse(
        id=publication.id,
        user_id=publication.user_id,
        project_id=publication.project_id,
        scene_take_id=publication.scene_take_id,
        asset_id=publication.asset_id,
        title=publication.title,
        description=publication.description,
        visibility=publication.visibility,
        is_explicit=publication.is_explicit,
        blur_required=publication.blur_required,
        allow_remix=publication.allow_remix,
        prompt_public=publication.prompt_public,
        status=publication.status,
        published_at=publication.published_at,
        media_url=media_url,
        preview_url=preview_url,
        blur_preview_url=blur_preview_url,
    )


async def _publication_derivative_urls(session: AsyncSession, asset_id: uuid.UUID) -> dict[str, str]:
    result = await session.execute(
        select(MediaDerivative).where(
            MediaDerivative.source_asset_id == asset_id,
            MediaDerivative.status == "ready",
        )
    )
    return {
        derivative.variant: f"/media/assets/{derivative.derivative_asset_id}/content"
        for derivative in result.scalars()
    }
