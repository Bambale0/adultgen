"""Aiogram-backed Telegram result delivery adapter."""

from __future__ import annotations

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup


class AiogramResultDeliveryClient:
    """Telegram Bot API delivery adapter built on aiogram Bot."""

    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def send_text(
        self,
        *,
        chat_id: int,
        text: str,
        reply_markup: object | None = None,
    ) -> int:
        """Send text message and return Telegram message id."""

        message = await self.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=_keyboard(reply_markup),
        )
        return message.message_id

    async def send_photo(
        self,
        *,
        chat_id: int,
        media: str,
        caption: str,
        reply_markup: object | None = None,
    ) -> int:
        """Send photo and return Telegram message id."""

        message = await self.bot.send_photo(
            chat_id=chat_id,
            photo=media,
            caption=caption,
            reply_markup=_keyboard(reply_markup),
        )
        return message.message_id

    async def send_video(
        self,
        *,
        chat_id: int,
        media: str,
        caption: str,
        reply_markup: object | None = None,
    ) -> int:
        """Send video and return Telegram message id."""

        message = await self.bot.send_video(
            chat_id=chat_id,
            video=media,
            caption=caption,
            reply_markup=_keyboard(reply_markup),
        )
        return message.message_id

    async def send_document(
        self,
        *,
        chat_id: int,
        media: str,
        caption: str,
        reply_markup: object | None = None,
    ) -> int:
        """Send document and return Telegram message id."""

        message = await self.bot.send_document(
            chat_id=chat_id,
            document=media,
            caption=caption,
            reply_markup=_keyboard(reply_markup),
        )
        return message.message_id


def _keyboard(reply_markup: object | None) -> InlineKeyboardMarkup | None:
    if reply_markup is None:
        return None
    if isinstance(reply_markup, InlineKeyboardMarkup):
        return reply_markup
    raise TypeError("reply_markup must be InlineKeyboardMarkup or None.")
