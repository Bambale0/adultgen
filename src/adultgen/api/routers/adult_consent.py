"""Adult consent API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.api.dependencies import (
    get_current_token_claims,
    get_db_session,
    get_runtime_settings,
)
from adultgen.api.schemas.adult_consent import (
    AdultConsentAcceptResponse,
    AdultConsentStatusResponse,
)
from adultgen.config import Settings
from adultgen.security.tokens import AccessTokenClaims
from adultgen.services.adult_consents import (
    accept_adult_consent,
    get_active_adult_consent,
)

router = APIRouter(prefix="/adult-consent", tags=["adult-consent"])


@router.get("", response_model=AdultConsentStatusResponse)
async def get_adult_consent_status(
    claims: Annotated[AccessTokenClaims, Depends(get_current_token_claims)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_runtime_settings)],
) -> AdultConsentStatusResponse:
    """Return whether the current user accepted the current adult policy."""

    consent = await get_active_adult_consent(
        session,
        user_id=claims.subject,
        policy_version=settings.adult_policy_version,
    )
    return AdultConsentStatusResponse(
        accepted=consent is not None,
        policy_version=settings.adult_policy_version,
        accepted_at=consent.accepted_at if consent else None,
    )


@router.post("/accept", response_model=AdultConsentAcceptResponse)
async def accept_current_adult_consent(
    claims: Annotated[AccessTokenClaims, Depends(get_current_token_claims)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_runtime_settings)],
) -> AdultConsentAcceptResponse:
    """Record adult policy acceptance for the current user."""

    consent = await accept_adult_consent(
        session,
        user_id=claims.subject,
        policy_version=settings.adult_policy_version,
    )
    return AdultConsentAcceptResponse(
        accepted=True,
        policy_version=consent.policy_version,
        accepted_at=consent.accepted_at,
    )
