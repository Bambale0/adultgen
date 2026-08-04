"""Telegram Mini App launch URL and button helpers."""

from __future__ import annotations

from enum import StrEnum
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo


class MiniAppButtonError(ValueError):
    """Raised when a Mini App launch URL cannot be built safely."""


class MiniAppSection(StrEnum):
    """First-class Mini App launch sections."""

    HOME = "home"
    FEED = "feed"
    CREATE = "create"
    PROJECTS = "projects"
    PROFILE = "profile"


_SECTION_PATHS = {
    MiniAppSection.HOME: "/",
    MiniAppSection.FEED: "/feed",
    MiniAppSection.CREATE: "/create",
    MiniAppSection.PROJECTS: "/projects",
}


def build_mini_app_url(
    base_url: str,
    *,
    section: MiniAppSection = MiniAppSection.HOME,
    profile_public_id: str | None = None,
    referral_code: str | None = None,
) -> str:
    """Build a safe Mini App URL for Telegram WebApp buttons."""

    parsed = urlsplit(base_url.strip())
    _validate_base_url(parsed.scheme, parsed.hostname)

    path = _section_path(section, profile_public_id=profile_public_id)
    root_path = parsed.path.rstrip("/")
    target_path = f"{root_path}{path}" if root_path else path

    query_items = dict(parse_qsl(parsed.query, keep_blank_values=False))
    if referral_code:
        query_items["ref"] = referral_code
    query = urlencode(query_items)

    return urlunsplit((parsed.scheme, parsed.netloc, target_path, query, ""))


def build_mini_app_main_menu(
    base_url: str,
    *,
    profile_public_id: str | None = None,
    referral_code: str | None = None,
) -> InlineKeyboardMarkup:
    """Build the default Telegram inline keyboard with Mini App launch buttons."""

    def web_app(section: MiniAppSection) -> WebAppInfo:
        return WebAppInfo(
            url=build_mini_app_url(
                base_url,
                section=section,
                referral_code=referral_code,
            )
        )

    rows = [
        [
            InlineKeyboardButton(
                text="🚀 Открыть приложение",
                web_app=web_app(MiniAppSection.HOME),
            )
        ],
        [
            InlineKeyboardButton(
                text="🎬 Создать",
                web_app=web_app(MiniAppSection.CREATE),
            ),
            InlineKeyboardButton(
                text="🔥 Лента",
                web_app=web_app(MiniAppSection.FEED),
            ),
        ],
        [
            InlineKeyboardButton(
                text="📁 Проекты",
                web_app=web_app(MiniAppSection.PROJECTS),
            )
        ],
    ]

    if profile_public_id:
        rows.append(
            [
                InlineKeyboardButton(
                    text="👤 Профиль автора",
                    web_app=WebAppInfo(
                        url=build_mini_app_url(
                            base_url,
                            section=MiniAppSection.PROFILE,
                            profile_public_id=profile_public_id,
                            referral_code=referral_code,
                        )
                    ),
                )
            ]
        )

    return InlineKeyboardMarkup(inline_keyboard=rows)


def _section_path(section: MiniAppSection, *, profile_public_id: str | None) -> str:
    if section == MiniAppSection.PROFILE:
        if not profile_public_id:
            raise MiniAppButtonError("profile_public_id is required for profile launch URL.")
        if "/" in profile_public_id or ".." in profile_public_id:
            raise MiniAppButtonError("profile_public_id must be path-safe.")
        return f"/u/{profile_public_id}"
    return _SECTION_PATHS[section]


def _validate_base_url(scheme: str, hostname: str | None) -> None:
    if not hostname:
        raise MiniAppButtonError("Mini App base URL must include a host.")
    if scheme == "https":
        return
    if scheme == "http" and hostname in {"localhost", "127.0.0.1"}:
        return
    raise MiniAppButtonError("Mini App base URL must use https outside local development.")
