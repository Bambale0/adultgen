"""Media upload and delivery API routes."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Header, HTTPException, Response, UploadFile, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.api.dependencies import get_current_token_claims, get_db_session, get_runtime_settings
from adultgen.api.schemas.media import MediaAssetResponse, MediaDerivativeResponse, MediaUploadResponse
from adultgen.api.storage import get_object_storage
from adultgen.config import Settings
from adultgen.db.models.media import MediaAsset, MediaDerivative
from adultgen.domain.media_storage import MediaBucketRole
from adultgen.security.tokens import AccessTokenClaims, TokenError, verify_access_token
from adultgen.services.media import MediaServiceError, UploadMediaCommand, upload_media_asset
from adultgen.services.media_derivatives import (
    MediaDerivativeError,
    MediaDerivativeVariant,
    ensure_media_derivative,
)
from adultgen.storage.ports import ObjectStorage

router = APIRouter(prefix="/media", tags=["media"])

MAX_UPLOAD_BYTES = 50 * 1024 * 1024


@router.post("/uploads/temporary", response_model=MediaUploadResponse)
async def upload_temporary_media(
    claims: Annotated[AccessTokenClaims, Depends(get_current_token_claims)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_runtime_settings)],
    storage: Annotated[ObjectStorage, Depends(get_object_storage)],
    file: Annotated[UploadFile, File()],
) -> MediaUploadResponse:
    """Upload temporary generation/reference media with 24h retention."""

    return await _upload_media(
        claims=claims,
        session=session,
        settings=settings,
        storage=storage,
        file=file,
        role=MediaBucketRole.TEMPORARY,
    )


@router.post("/uploads/references", response_model=MediaUploadResponse)
async def upload_reference_media(
    claims: Annotated[AccessTokenClaims, Depends(get_current_token_claims)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_runtime_settings)],
    storage: Annotated[ObjectStorage, Depends(get_object_storage)],
    file: Annotated[UploadFile, File()],
) -> MediaUploadResponse:
    """Upload durable private reference media for avatars/scenes."""

    return await _upload_media(
        claims=claims,
        session=session,
        settings=settings,
        storage=storage,
        file=file,
        role=MediaBucketRole.REFERENCES,
    )


@router.post("/assets/{asset_id}/derivatives/{variant}", response_model=MediaDerivativeResponse)
async def create_media_derivative(
    asset_id: uuid.UUID,
    variant: MediaDerivativeVariant,
    claims: Annotated[AccessTokenClaims, Depends(get_current_token_claims)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_runtime_settings)],
    storage: Annotated[ObjectStorage, Depends(get_object_storage)],
) -> MediaDerivativeResponse:
    """Create or return a preview/blur derivative for an owned published asset."""

    asset = await _get_asset(session, asset_id)
    if asset.owner_user_id != claims.subject:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Media asset is not owned by user.")

    try:
        derivative = await ensure_media_derivative(
            session,
            storage=storage,
            settings=settings,
            source_asset_id=asset_id,
            variant=variant,
        )
    except MediaDerivativeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return _derivative_response(derivative)


@router.get("/assets/{asset_id}/content")
async def get_media_asset_content(
    asset_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_runtime_settings)],
    storage: Annotated[ObjectStorage, Depends(get_object_storage)],
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> Response:
    """Serve media bytes through the Core API delivery boundary.

    Published media is public by UUID. Temporary/reference media requires the owning
    user's bearer token. Provider-CDN results are exposed through a short redirect.
    """

    asset = await _get_asset(session, asset_id)
    if asset.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found.")

    is_published = asset.storage_bucket == settings.s3_published_bucket
    if not is_published:
        claims = _optional_claims(authorization, settings=settings)
        if claims is None or asset.owner_user_id != claims.subject:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Media asset is private.")

    if asset.external_url:
        return RedirectResponse(
            url=asset.external_url,
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Cache-Control": "no-store", "X-AdultGen-Media-Id": str(asset.id)},
        )

    try:
        stored = await storage.get_object(
            bucket=asset.storage_bucket,
            key=asset.storage_key,
            content_type=asset.mime_type,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media object not found.") from exc

    return Response(
        content=stored.body,
        media_type=stored.content_type,
        headers={
            "Cache-Control": "public, max-age=300" if is_published else "no-store",
            "X-AdultGen-Media-Id": str(asset.id),
        },
    )


async def _upload_media(
    *,
    claims: AccessTokenClaims,
    session: AsyncSession,
    settings: Settings,
    storage: ObjectStorage,
    file: UploadFile,
    role: MediaBucketRole,
) -> MediaUploadResponse:
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Uploaded file is too large.")

    try:
        asset = await upload_media_asset(
            session,
            storage=storage,
            settings=settings,
            command=UploadMediaCommand(
                owner_user_id=claims.subject,
                raw=raw,
                filename=file.filename,
                mime_type=file.content_type,
                role=role,
            ),
        )
    except MediaServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return MediaUploadResponse(asset=_asset_response(asset))


async def _get_asset(session: AsyncSession, asset_id: uuid.UUID) -> MediaAsset:
    result = await session.execute(select(MediaAsset).where(MediaAsset.id == asset_id))
    asset = result.scalar_one_or_none()
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found.")
    return asset


def _optional_claims(authorization: str | None, *, settings: Settings) -> AccessTokenClaims | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return verify_access_token(token, secret=settings.jwt_secret)
    except TokenError:
        return None


def _asset_response(asset: object) -> MediaAssetResponse:
    return MediaAssetResponse(
        id=asset.id,
        storage_bucket=asset.storage_bucket,
        storage_key=asset.storage_key,
        media_type=asset.media_type,
        mime_type=asset.mime_type,
        size_bytes=asset.size_bytes,
        checksum_sha256=asset.checksum_sha256,
        is_temporary=asset.is_temporary,
        expires_at=asset.expires_at,
        deleted_at=asset.deleted_at,
    )


def _derivative_response(derivative: MediaDerivative) -> MediaDerivativeResponse:
    return MediaDerivativeResponse(
        id=derivative.id,
        source_asset_id=derivative.source_asset_id,
        derivative_asset_id=derivative.derivative_asset_id,
        variant=derivative.variant,
        status=derivative.status,
        processor_version=derivative.processor_version,
        media_url=f"/media/assets/{derivative.derivative_asset_id}/content",
    )
