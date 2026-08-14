"""Telegram Login Widget payload verification."""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from time import time


class TelegramLoginError(ValueError):
    """Raised when Login Widget data is invalid or stale."""


@dataclass(frozen=True, slots=True)
class TelegramLoginUser:
    """Verified Telegram website identity."""

    id: int
    first_name: str
    last_name: str | None
    username: str | None
    photo_url: str | None
    auth_date: int


def verify_telegram_login_payload(
    payload: dict[str, object],
    *,
    bot_token: str,
    max_age_seconds: int,
    now: int | None = None,
) -> TelegramLoginUser:
    """Validate Telegram's HMAC signature and freshness guarantee."""

    if not bot_token:
        raise TelegramLoginError("Telegram login is not configured.")

    received_hash = str(payload.get("hash") or "")
    if len(received_hash) != 64:
        raise TelegramLoginError("Telegram login hash is missing or malformed.")

    signed_fields = {
        key: value
        for key, value in payload.items()
        if key not in {"hash", "referral_payload"} and value is not None
    }
    data_check_string = "\n".join(f"{key}={signed_fields[key]}" for key in sorted(signed_fields))
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_hash, received_hash):
        raise TelegramLoginError("Telegram login signature is invalid.")

    try:
        telegram_user_id = int(signed_fields["id"])
        auth_date = int(signed_fields["auth_date"])
    except (KeyError, TypeError, ValueError) as exc:
        raise TelegramLoginError("Telegram login identity fields are invalid.") from exc

    current_time = int(time()) if now is None else now
    if auth_date > current_time + 30 or (max_age_seconds > 0 and current_time - auth_date > max_age_seconds):
        raise TelegramLoginError("Telegram login data is stale.")

    first_name = str(signed_fields.get("first_name") or "").strip()
    if telegram_user_id <= 0 or not first_name:
        raise TelegramLoginError("Telegram login identity fields are invalid.")

    return TelegramLoginUser(
        id=telegram_user_id,
        first_name=first_name,
        last_name=_optional_string(signed_fields.get("last_name")),
        username=_optional_string(signed_fields.get("username")),
        photo_url=_optional_string(signed_fields.get("photo_url")),
        auth_date=auth_date,
    )


def _optional_string(value: object) -> str | None:
    normalized = str(value or "").strip()
    return normalized or None
