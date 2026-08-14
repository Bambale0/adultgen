import hashlib
import hmac

import pytest

from adultgen.integrations.telegram.login_widget import (
    TelegramLoginError,
    verify_telegram_login_payload,
)


def signed_payload(*, bot_token: str, auth_date: int) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": 123456789,
        "first_name": "Creator",
        "username": "adultgen_creator",
        "auth_date": auth_date,
    }
    check = "\n".join(f"{key}={payload[key]}" for key in sorted(payload))
    secret = hashlib.sha256(bot_token.encode()).digest()
    payload["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return payload


def test_login_widget_accepts_fresh_signed_payload() -> None:
    payload = signed_payload(bot_token="123:secret", auth_date=1_700_000_000)

    user = verify_telegram_login_payload(
        payload,
        bot_token="123:secret",
        max_age_seconds=900,
        now=1_700_000_300,
    )

    assert user.id == 123456789
    assert user.username == "adultgen_creator"


def test_login_widget_rejects_tampering_and_stale_data() -> None:
    payload = signed_payload(bot_token="123:secret", auth_date=1_700_000_000)
    payload["first_name"] = "Attacker"
    with pytest.raises(TelegramLoginError, match="signature"):
        verify_telegram_login_payload(
            payload,
            bot_token="123:secret",
            max_age_seconds=900,
            now=1_700_000_300,
        )

    stale = signed_payload(bot_token="123:secret", auth_date=1_700_000_000)
    with pytest.raises(TelegramLoginError, match="stale"):
        verify_telegram_login_payload(
            stale,
            bot_token="123:secret",
            max_age_seconds=900,
            now=1_700_002_000,
        )
