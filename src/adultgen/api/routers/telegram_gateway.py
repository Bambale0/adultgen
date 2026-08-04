"""Telegram webhook gateway routes."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.api.dependencies import get_db_session
from adultgen.services.users import (
    UserServiceError,
    get_active_telegram_channel,
    record_user_channel_activity,
    upsert_user_from_telegram,
)
from adultgen.telegram_gateway.security import (
    TelegramWebhookSecurityError,
    verify_webhook_secret,
)
from adultgen.telegram_gateway.updates import TelegramUpdateError, summarize_update

router = APIRouter(prefix="/telegram", tags=["telegram-gateway"])


@router.post("/webhook/{bot_username}")
async def telegram_webhook(
    bot_username: str,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    telegram_secret_token: Annotated[
        str | None,
        Header(alias="X-Telegram-Bot-Api-Secret-Token"),
    ] = None,
) -> dict[str, Any]:
    """Receive one Telegram webhook update for a specific bot mirror."""

    try:
        channel = await get_active_telegram_channel(session, bot_username=bot_username)
        verify_webhook_secret(
            provided_secret=telegram_secret_token,
            expected_hash=channel.webhook_secret_hash,
        )
        payload = await request.json()
        if not isinstance(payload, dict):
            raise TelegramUpdateError("Telegram webhook payload must be a JSON object.")
        summary = summarize_update(payload)
        tracked_user_id = None
        if summary.telegram_user is not None:
            user = await upsert_user_from_telegram(
                session,
                telegram_user=summary.telegram_user,
            )
            tracked_user_id = user.id
            await record_user_channel_activity(
                session,
                user_id=user.id,
                telegram_channel_id=channel.id,
                telegram_chat_id=summary.message_chat_id,
                start_payload=summary.start_payload,
            )
    except UserServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except TelegramWebhookSecurityError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    except TelegramUpdateError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    parsed_start_payload = summary.parsed_start_payload
    return {
        "ok": True,
        "bot_username": channel.bot_username,
        "update_id": summary.update_id,
        "message_chat_id": summary.message_chat_id,
        "tracked_user_id": str(tracked_user_id) if tracked_user_id else None,
        "start_payload": summary.start_payload,
        "start_payload_kind": parsed_start_payload.kind.value if parsed_start_payload else None,
        "profile_public_id": (
            parsed_start_payload.profile_public_id if parsed_start_payload else None
        ),
        "referral_code": parsed_start_payload.referral_code if parsed_start_payload else None,
    }
