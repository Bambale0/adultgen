"""Telegram update parsing helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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


def summarize_update(payload: dict[str, Any]) -> TelegramUpdateSummary:
    """Extract routing-relevant fields from a Telegram update payload."""

    raw_update_id = payload.get("update_id")
    if not isinstance(raw_update_id, int):
        raise TelegramUpdateError("Telegram update_id is required.")

    message = payload.get("message") or payload.get("edited_message")
    message_chat_id = _extract_chat_id(message)
    start_payload = _extract_start_payload(message)

    return TelegramUpdateSummary(
        update_id=raw_update_id,
        message_chat_id=message_chat_id,
        start_payload=start_payload,
        parsed_start_payload=parse_start_payload(start_payload),
    )


def _extract_chat_id(message: object) -> int | None:
    if not isinstance(message, dict):
        return None
    chat = message.get("chat")
    if not isinstance(chat, dict):
        return None
    chat_id = chat.get("id")
    return chat_id if isinstance(chat_id, int) else None


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
