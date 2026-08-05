"""Media upload API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.api.dependencies import get_current_token_claims, get_db_session, get_runtime_settings
from adultgen.api.schemas.media import MediaAssetResponse, MediaUploadResponse
from adultgen.api.storage import get_object_storage
from adultgen.config import Settings
from adultgen.domain.media_storage import MediaBucketRole
from adultgen.security.tokens import AccessTokenClaims
from adultgen.services.media import MediaServiceError, UploadMediaCommand, upload_media_asset
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
