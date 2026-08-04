"""Telegram update parsing helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from adultgen.integrations.telegram.mini_app_auth import TelegramMiniAppUser
from adultgen.telegram_gateway.start_payload import StartPayload, parse_start_payload


class TelegramUpdateError(ValueError):
    """Raised when an incoming Telegram update is malformed."""


@dataclass(frozen=True, slots=True)
class TelegramUpdateSummary:
    """Small update summary stored/returned by the gateway boundary."""

    update_id: int
    message_chat_id: int | None
    start_payload: str | None
    parsed_start_payload: StartPayload | None
    telegram_user: TelegramMiniAppUser | None


def summarize_update(payload: dict[str, Any]) -> TelegramUpdateSummary:
    """Extract routing-relevant fields from a Telegram update payload."""

    raw_update_id = payload.get("update_id")
    if not isinstance(raw_update_id, int):
        raise TelegramUpdateError("Telegram update_id is required.")

    message = payload.get("message") or payload.get("edited_message")
    callback_query = payload.get("callback_query")
    message_chat_id = _extract_chat_id(message) or _extract_callback_chat_id(callback_query)
    start_payload = _extract_start_payload(message)

    return TelegramUpdateSummary(
        update_id=raw_update_id,
        message_chat_id=message_chat_id,
        start_payload=start_payload,
        parsed_start_payload=parse_start_payload(start_payload),
        telegram_user=_extract_user(message) or _extract_user(callback_query),
    )


def _extract_chat_id(message: object) -> int | None:
    if not isinstance(message, dict):
        return None
    chat = message.get("chat")
    if not isinstance(chat, dict):
        return None
    chat_id = chat.get("id")
    return chat_id if isinstance(chat_id, int) else None


def _extract_callback_chat_id(callback_query: object) -> int | None:
    if not isinstance(callback_query, dict):
        return None
    return _extract_chat_id(callback_query.get("message"))


def _extract_start_payload(message: object) -> str | None:
    if not isinstance(message, dict):
        return None
    text = message.get("text")
    if not isinstance(text, str):
        return None
    if text == "/start":
        return None
    if text.startswith("/start "):
        return text.removeprefix("/start ").strip() or None
    return None


def _extract_user(update_part: object) -> TelegramMiniAppUser | None:
    if not isinstance(update_part, dict):
        return None
    user_payload = update_part.get("from")
    if not isinstance(user_payload, dict):
        return None
    user_id = user_payload.get("id")
    if not isinstance(user_id, int):
        return None
    return TelegramMiniAppUser(
        id=user_id,
        username=_optional_str(user_payload.get("username")),
        first_name=_optional_str(user_payload.get("first_name")),
        last_name=_optional_str(user_payload.get("last_name")),
        language_code=_optional_str(user_payload.get("language_code")),
    )


def _optional_str(value: object) -> str | None:
    return value if isinstance(value, str) else None
