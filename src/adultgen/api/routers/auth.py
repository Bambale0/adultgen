"""Authentication routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.api.dependencies import get_db_session, get_runtime_settings
from adultgen.api.schemas.auth import (
    TelegramMiniAppAuthRequest,
    TelegramMiniAppAuthResponse,
    UserCapabilityResponse,
)
from adultgen.config import Settings
from adultgen.integrations.telegram.mini_app_auth import (
    TelegramMiniAppAuthError,
    verify_telegram_mini_app_init_data,
)
from adultgen.security.tokens import create_access_token
from adultgen.services.users import (
    BotTokenResolver,
    UserServiceError,
    get_active_telegram_channel,
    record_user_channel_activity,
    upsert_user_from_telegram,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/telegram-mini-app", response_model=TelegramMiniAppAuthResponse)
async def authenticate_telegram_mini_app(
    payload: TelegramMiniAppAuthRequest,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_runtime_settings),
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
        capabilities=UserCapabilityResponse(
            can_generate=user.can_generate,
            can_publish_profile=user.can_publish_profile,
            can_publish_feed=user.can_publish_feed,
            can_use_payments=user.can_use_payments,
        ),
    )
