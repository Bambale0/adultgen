"""Telegram result delivery domain/service helpers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class ResultDeliveryError(ValueError):
    """Raised when result delivery cannot be planned or completed."""


class TelegramDeliveryMediaKind(StrEnum):
    """Media kinds supported by Telegram result delivery."""

    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"
    TEXT = "text"


@dataclass(frozen=True, slots=True)
class ResultDeliveryCommand:
    """Command describing one result notification to Telegram."""

    chat_id: int
    media_kind: TelegramDeliveryMediaKind
    caption: str
    media_url: str | None = None
    telegram_file_id: str | None = None
    reply_markup: object | None = None


@dataclass(frozen=True, slots=True)
class ResultDeliveryResult:
    """Minimal successful Telegram delivery result."""

    chat_id: int
    telegram_message_id: int
    media_kind: TelegramDeliveryMediaKind


class TelegramResultClient(Protocol):
    """Port implemented by Telegram Bot API adapters."""

    async def send_text(
        self,
        *,
        chat_id: int,
        text: str,
        reply_markup: object | None = None,
    ) -> int:
        """Send a text message and return Telegram message id."""

    async def send_photo(
        self,
        *,
        chat_id: int,
        media: str,
        caption: str,
        reply_markup: object | None = None,
    ) -> int:
        """Send a photo and return Telegram message id."""

    async def send_video(
        self,
        *,
        chat_id: int,
        media: str,
        caption: str,
        reply_markup: object | None = None,
    ) -> int:
        """Send a video and return Telegram message id."""

    async def send_document(
        self,
        *,
        chat_id: int,
        media: str,
        caption: str,
        reply_markup: object | None = None,
    ) -> int:
        """Send a document and return Telegram message id."""


async def deliver_generation_result(
    client: TelegramResultClient,
    *,
    command: ResultDeliveryCommand,
) -> ResultDeliveryResult:
    """Deliver a generated result to Telegram using the proper send method."""

    _validate_command(command)

    match command.media_kind:
        case TelegramDeliveryMediaKind.TEXT:
            message_id = await client.send_text(
                chat_id=command.chat_id,
                text=command.caption,
                reply_markup=command.reply_markup,
            )
        case TelegramDeliveryMediaKind.IMAGE:
            message_id = await client.send_photo(
                chat_id=command.chat_id,
                media=_media_reference(command),
                caption=command.caption,
                reply_markup=command.reply_markup,
            )
        case TelegramDeliveryMediaKind.VIDEO:
            message_id = await client.send_video(
                chat_id=command.chat_id,
                media=_media_reference(command),
                caption=command.caption,
                reply_markup=command.reply_markup,
            )
        case TelegramDeliveryMediaKind.DOCUMENT:
            message_id = await client.send_document(
                chat_id=command.chat_id,
                media=_media_reference(command),
                caption=command.caption,
                reply_markup=command.reply_markup,
            )

    return ResultDeliveryResult(
        chat_id=command.chat_id,
        telegram_message_id=message_id,
        media_kind=command.media_kind,
    )


def _validate_command(command: ResultDeliveryCommand) -> None:
    if command.chat_id == 0:
        raise ResultDeliveryError("Telegram chat_id cannot be zero.")
    if not command.caption.strip():
        raise ResultDeliveryError("Telegram delivery caption/text cannot be empty.")
    if command.media_kind != TelegramDeliveryMediaKind.TEXT and not _media_reference(command):
        raise ResultDeliveryError("Media delivery requires media_url or telegram_file_id.")


def _media_reference(command: ResultDeliveryCommand) -> str:
    return command.telegram_file_id or command.media_url or ""
