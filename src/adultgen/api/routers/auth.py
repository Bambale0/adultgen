"""Authentication routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.api.dependencies import get_db_session, get_runtime_settings
from adultgen.api.schemas.auth import (
    GoogleAuthRequest,
    TelegramMiniAppAuthRequest,
    TelegramMiniAppAuthResponse,
    TelegramLoginAuthRequest,
    UserCapabilityResponse,
    WebsiteAuthResponse,
)
from adultgen.config import Settings
from adultgen.integrations.google_auth import GoogleIdentityError, verify_google_identity_token
from adultgen.integrations.telegram.login_widget import TelegramLoginError, verify_telegram_login_payload
from adultgen.integrations.telegram.mini_app_auth import (
    TelegramMiniAppAuthError,
    TelegramMiniAppUser,
    verify_telegram_mini_app_init_data,
)
from adultgen.security.tokens import create_access_token
from adultgen.services.users import (
    AuthenticatedUser,
    BotTokenResolver,
    UserServiceError,
    get_active_telegram_channel,
    record_user_channel_activity,
    upsert_user_from_external_identity,
    upsert_user_from_telegram,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/telegram-mini-app", response_model=TelegramMiniAppAuthResponse)
async def authenticate_telegram_mini_app(
    payload: TelegramMiniAppAuthRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_runtime_settings)],
) -> TelegramMiniAppAuthResponse:
    """Authenticate Mini App initData and return a Core API access token."""

    try:
        channel = await get_active_telegram_channel(session, bot_username=payload.bot_username)
        bot_token = BotTokenResolver(settings).resolve(channel.secret_ref)
        verified = verify_telegram_mini_app_init_data(
            payload.init_data,
            bot_token=bot_token,
            max_age_seconds=settings.mini_app_auth_max_age_seconds,
        )
        user = await upsert_user_from_telegram(session, telegram_user=verified.user)
        await record_user_channel_activity(
            session,
            user_id=user.id,
            telegram_channel_id=channel.id,
            telegram_chat_id=None,
            start_payload=payload.start_payload or verified.start_param,
        )
    except TelegramMiniAppAuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    except UserServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    access_token = create_access_token(
        subject=user.id,
        telegram_user_id=user.telegram_user_id,
        secret=settings.jwt_secret,
        ttl_seconds=settings.jwt_access_token_ttl_seconds,
    )

    return TelegramMiniAppAuthResponse(
        access_token=access_token,
        user_id=user.id,
        telegram_user_id=user.telegram_user_id,
        is_blocked=user.is_blocked,
        capabilities=_capabilities_response(user),
    )


@router.post("/google", response_model=WebsiteAuthResponse)
async def authenticate_google(
    payload: GoogleAuthRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_runtime_settings)],
) -> WebsiteAuthResponse:
    """Exchange a verified Google ID token for a short-lived Core API token."""

    try:
        identity = await verify_google_identity_token(
            payload.credential,
            client_id=settings.google_oauth_client_id,
        )
        user = await upsert_user_from_external_identity(
            session,
            provider="google",
            subject=identity.subject,
            display_name=identity.display_name,
        )
    except (GoogleIdentityError, UserServiceError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    return _website_auth_response(
        user,
        settings=settings,
        provider="google",
        email=identity.email,
        display_name=identity.display_name,
    )


@router.post("/telegram-login", response_model=WebsiteAuthResponse)
async def authenticate_telegram_login(
    payload: TelegramLoginAuthRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_runtime_settings)],
) -> WebsiteAuthResponse:
    """Exchange signed Telegram Login Widget data for a Core API token."""

    try:
        telegram_login = verify_telegram_login_payload(
            payload.model_dump(exclude_none=True),
            bot_token=settings.telegram_default_bot_token,
            max_age_seconds=settings.telegram_login_max_age_seconds,
        )
        telegram_user = TelegramMiniAppUser(
            id=telegram_login.id,
            first_name=telegram_login.first_name,
            last_name=telegram_login.last_name,
            username=telegram_login.username,
        )
        user = await upsert_user_from_telegram(
            session,
            telegram_user=telegram_user,
        )
    except (TelegramLoginError, UserServiceError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    display_name = " ".join(filter(None, [telegram_login.first_name, telegram_login.last_name])).strip()
    return _website_auth_response(
        user,
        settings=settings,
        provider="telegram",
        email=None,
        display_name=display_name,
    )


def _website_auth_response(
    user: AuthenticatedUser,
    *,
    settings: Settings,
    provider: str,
    email: str | None,
    display_name: str,
) -> WebsiteAuthResponse:
    access_token = create_access_token(
        subject=user.id,
        telegram_user_id=user.telegram_user_id,
        secret=settings.jwt_secret,
        ttl_seconds=settings.jwt_access_token_ttl_seconds,
    )
    return WebsiteAuthResponse(
        access_token=access_token,
        user_id=user.id,
        telegram_user_id=user.telegram_user_id,
        is_blocked=user.is_blocked,
        capabilities=_capabilities_response(user),
        provider=provider,
        email=email,
        display_name=display_name,
    )


def _capabilities_response(user: AuthenticatedUser) -> UserCapabilityResponse:
    return UserCapabilityResponse(
        can_generate=user.can_generate,
        can_publish_profile=user.can_publish_profile,
        can_publish_feed=user.can_publish_feed,
        can_use_payments=user.can_use_payments,
    )
