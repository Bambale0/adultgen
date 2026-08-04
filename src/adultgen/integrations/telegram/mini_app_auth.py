"""Telegram Mini App initData verification.

Telegram signs Mini App initData with a secret derived from the bot token. The
backend must validate the hash for the exact bot channel that opened the Mini App.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl


class TelegramMiniAppAuthError(ValueError):
    """Raised when Telegram Mini App initData is invalid."""


@dataclass(frozen=True, slots=True)
class TelegramMiniAppUser:
    """User payload embedded into Telegram Mini App initData."""

    id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    language_code: str | None = None


@dataclass(frozen=True, slots=True)
class TelegramMiniAppAuthData:
    """Verified Mini App auth data."""

    user: TelegramMiniAppUser
    auth_date: int
    query_id: str | None
    start_param: str | None
    raw: dict[str, str]


def verify_telegram_mini_app_init_data(
    init_data: str,
    *,
    bot_token: str,
    max_age_seconds: int,
    now_ts: int | None = None,
) -> TelegramMiniAppAuthData:
    """Verify Telegram Mini App initData and return normalized auth data."""

    if not init_data:
        raise TelegramMiniAppAuthError("initData is empty.")
    if not bot_token:
        raise TelegramMiniAppAuthError("Bot token is empty.")

    pairs = dict(parse_qsl(init_data, keep_blank_values=True, strict_parsing=True))
    received_hash = pairs.get("hash")
    if not received_hash:
        raise TelegramMiniAppAuthError("initData hash is missing.")

    data_check_string = "\n".join(
        f"{key}={value}"
        for key, value in sorted(pairs.items())
        if key not in {"hash", "signature"}
    )
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise TelegramMiniAppAuthError("initData hash is invalid.")

    auth_date = _require_int(pairs, "auth_date")
    now = int(now_ts or time.time())
    if max_age_seconds > 0 and now - auth_date > max_age_seconds:
        raise TelegramMiniAppAuthError("initData is too old.")

    user = _parse_user(pairs.get("user"))
    return TelegramMiniAppAuthData(
        user=user,
        auth_date=auth_date,
        query_id=pairs.get("query_id"),
        start_param=pairs.get("start_param"),
        raw=pairs,
    )


def _require_int(pairs: dict[str, str], key: str) -> int:
    raw_value = pairs.get(key)
    if raw_value is None:
        raise TelegramMiniAppAuthError(f"initData {key!r} is missing.")
    try:
        return int(raw_value)
    except ValueError as exc:
        raise TelegramMiniAppAuthError(f"initData {key!r} must be an integer.") from exc


def _parse_user(raw_user: str | None) -> TelegramMiniAppUser:
    if not raw_user:
        raise TelegramMiniAppAuthError("initData user is missing.")

    try:
        user_payload = json.loads(raw_user)
    except json.JSONDecodeError as exc:
        raise TelegramMiniAppAuthError("initData user is not valid JSON.") from exc

    if not isinstance(user_payload, dict):
        raise TelegramMiniAppAuthError("initData user must be an object.")

    try:
        telegram_user_id = int(user_payload["id"])
    except (KeyError, TypeError, ValueError) as exc:
        raise TelegramMiniAppAuthError("initData user.id is invalid.") from exc

    return TelegramMiniAppUser(
        id=telegram_user_id,
        username=_optional_string(user_payload.get("username")),
        first_name=_optional_string(user_payload.get("first_name")),
        last_name=_optional_string(user_payload.get("last_name")),
        language_code=_optional_string(user_payload.get("language_code")),
    )


def _optional_string(value: object) -> str | None:
    return value if isinstance(value, str) and value else None
