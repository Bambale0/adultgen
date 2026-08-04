"""Telegram result delivery API routes."""

from typing import Annotated

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.api.dependencies import (
    get_db_session,
    get_runtime_settings,
    require_admin_api_token,
)
from adultgen.api.schemas.telegram_delivery import (
    TelegramResultDeliveryRequest,
    TelegramResultDeliveryResponse,
)
from adultgen.config import Settings
from adultgen.services.users import (
    BotTokenResolver,
    UserServiceError,
    get_active_telegram_channel,
)
from adultgen.telegram_gateway.aiogram_delivery import AiogramResultDeliveryClient
from adultgen.telegram_gateway.mini_app_buttons import build_mini_app_main_menu
from adultgen.telegram_gateway.result_delivery import (
    ResultDeliveryCommand,
    ResultDeliveryError,
    deliver_generation_result,
)

router = APIRouter(
    prefix="/telegram/deliveries",
    tags=["telegram-deliveries"],
    dependencies=[Depends(require_admin_api_token)],
)


@router.post("/result", response_model=TelegramResultDeliveryResponse)
async def deliver_telegram_result(
    payload: TelegramResultDeliveryRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_runtime_settings)],
) -> TelegramResultDeliveryResponse:
    """Deliver one generated result to a Telegram chat through a bot channel."""

    try:
        channel = await get_active_telegram_channel(session, bot_username=payload.bot_username)
        bot_token = BotTokenResolver(settings).resolve(channel.secret_ref)
        reply_markup = None
        if payload.include_mini_app_buttons and channel.mini_app_url:
            reply_markup = build_mini_app_main_menu(
                channel.mini_app_url,
                profile_public_id=payload.profile_public_id,
                referral_code=payload.referral_code,
            )

        bot = Bot(token=bot_token)
        try:
            result = await deliver_generation_result(
                AiogramResultDeliveryClient(bot),
                command=ResultDeliveryCommand(
                    chat_id=payload.chat_id,
                    media_kind=payload.media_kind,
                    caption=payload.caption,
                    media_url=payload.media_url,
                    telegram_file_id=payload.telegram_file_id,
                    reply_markup=reply_markup,
                ),
            )
        finally:
            await bot.session.close()
    except UserServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ResultDeliveryError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except TelegramAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Telegram delivery failed.",
        ) from exc

    return TelegramResultDeliveryResponse(
        ok=True,
        bot_username=channel.bot_username,
        chat_id=result.chat_id,
        telegram_message_id=result.telegram_message_id,
        media_kind=result.media_kind,
    )
