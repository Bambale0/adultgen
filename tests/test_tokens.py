import uuid

import pytest

from adultgen.security.tokens import TokenError, create_access_token, verify_access_token


def test_access_token_round_trip() -> None:
    user_id = uuid.uuid4()
    token = create_access_token(
        subject=user_id,
        telegram_user_id=42,
        secret="secret",
        ttl_seconds=60,
        now_ts=1_700_000_000,
    )

    claims = verify_access_token(token, secret="secret", now_ts=1_700_000_010)

    assert claims.subject == user_id
    assert claims.telegram_user_id == 42
    assert claims.issued_at == 1_700_000_000
    assert claims.expires_at == 1_700_000_060


def test_access_token_rejects_wrong_secret() -> None:
    token = create_access_token(
        subject=uuid.uuid4(),
        telegram_user_id=42,
        secret="secret",
        ttl_seconds=60,
        now_ts=1_700_000_000,
    )

    with pytest.raises(TokenError, match="signature"):
        verify_access_token(token, secret="wrong", now_ts=1_700_000_010)


def test_access_token_rejects_expired_token() -> None:
    token = create_access_token(
        subject=uuid.uuid4(),
        telegram_user_id=42,
        secret="secret",
        ttl_seconds=5,
        now_ts=1_700_000_000,
    )

    with pytest.raises(TokenError, match="expired"):
        verify_access_token(token, secret="secret", now_ts=1_700_000_010)
