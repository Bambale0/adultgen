import hashlib
import hmac
import json
from urllib.parse import urlencode

import pytest

from adultgen.integrations.telegram.mini_app_auth import (
    TelegramMiniAppAuthError,
    verify_telegram_mini_app_init_data,
)


def test_verify_telegram_mini_app_init_data_accepts_valid_hash() -> None:
    bot_token = "123456:test-token"
    init_data = _make_init_data(
        bot_token,
        auth_date=1_700_000_000,
        user={
            "id": 42,
            "username": "igor",
            "first_name": "Igor",
            "language_code": "ru",
        },
        start_param="profile_abc",
    )

    result = verify_telegram_mini_app_init_data(
        init_data,
        bot_token=bot_token,
        max_age_seconds=86_400,
        now_ts=1_700_000_010,
    )

    assert result.user.id == 42
    assert result.user.username == "igor"
    assert result.user.first_name == "Igor"
    assert result.user.language_code == "ru"
    assert result.start_param == "profile_abc"


def test_verify_telegram_mini_app_init_data_rejects_tampered_hash() -> None:
    bot_token = "123456:test-token"
    init_data = _make_init_data(
        bot_token,
        auth_date=1_700_000_000,
        user={"id": 42, "first_name": "Igor"},
    ).replace("Igor", "Evil")

    with pytest.raises(TelegramMiniAppAuthError, match="hash is invalid"):
        verify_telegram_mini_app_init_data(
            init_data,
            bot_token=bot_token,
            max_age_seconds=86_400,
            now_ts=1_700_000_010,
        )


def test_verify_telegram_mini_app_init_data_rejects_stale_auth_date() -> None:
    bot_token = "123456:test-token"
    init_data = _make_init_data(
        bot_token,
        auth_date=1_700_000_000,
        user={"id": 42, "first_name": "Igor"},
    )

    with pytest.raises(TelegramMiniAppAuthError, match="too old"):
        verify_telegram_mini_app_init_data(
            init_data,
            bot_token=bot_token,
            max_age_seconds=5,
            now_ts=1_700_000_010,
        )


def _make_init_data(
    bot_token: str,
    *,
    auth_date: int,
    user: dict[str, object],
    start_param: str | None = None,
) -> str:
    payload = {
        "auth_date": str(auth_date),
        "query_id": "AAEAAAE",
        "user": json.dumps(user, separators=(",", ":"), sort_keys=True),
    }
    if start_param:
        payload["start_param"] = start_param

    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(payload.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    payload["hash"] = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()
    return urlencode(payload)
