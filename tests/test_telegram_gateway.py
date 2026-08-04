import pytest

from adultgen.telegram_gateway.dispatcher import create_dispatcher
from adultgen.telegram_gateway.security import (
    TelegramWebhookSecurityError,
    hash_webhook_secret,
    verify_webhook_secret,
)
from adultgen.telegram_gateway.start_payload import StartPayloadKind
from adultgen.telegram_gateway.updates import TelegramUpdateError, summarize_update


def test_webhook_secret_hash_verification_accepts_matching_secret() -> None:
    expected_hash = hash_webhook_secret("secret-token")

    verify_webhook_secret(
        provided_secret="secret-token",
        expected_hash=expected_hash,
    )


def test_webhook_secret_hash_verification_rejects_wrong_secret() -> None:
    expected_hash = hash_webhook_secret("secret-token")

    with pytest.raises(TelegramWebhookSecurityError, match="Invalid"):
        verify_webhook_secret(
            provided_secret="wrong-token",
            expected_hash=expected_hash,
        )


def test_summarize_update_extracts_chat_id_start_payload_and_user() -> None:
    summary = summarize_update(
        {
            "update_id": 123,
            "message": {
                "from": {
                    "id": 777,
                    "username": "creator",
                    "first_name": "Ann",
                    "language_code": "ru",
                },
                "chat": {"id": 456},
                "text": "/start profile_abc123",
            },
        }
    )

    assert summary.update_id == 123
    assert summary.message_chat_id == 456
    assert summary.start_payload == "profile_abc123"
    assert summary.parsed_start_payload is not None
    assert summary.parsed_start_payload.kind == StartPayloadKind.PROFILE
    assert summary.parsed_start_payload.profile_public_id == "abc123"
    assert summary.telegram_user is not None
    assert summary.telegram_user.id == 777
    assert summary.telegram_user.username == "creator"
    assert summary.telegram_user.first_name == "Ann"
    assert summary.telegram_user.language_code == "ru"


def test_summarize_update_extracts_callback_query_user_and_chat_id() -> None:
    summary = summarize_update(
        {
            "update_id": 124,
            "callback_query": {
                "from": {"id": 888, "username": "viewer"},
                "message": {"chat": {"id": 999}},
                "data": "noop",
            },
        }
    )

    assert summary.update_id == 124
    assert summary.message_chat_id == 999
    assert summary.telegram_user is not None
    assert summary.telegram_user.id == 888
    assert summary.telegram_user.username == "viewer"


def test_summarize_update_accepts_non_start_messages() -> None:
    summary = summarize_update(
        {
            "update_id": 123,
            "message": {
                "chat": {"id": 456},
                "text": "hello",
            },
        }
    )

    assert summary.update_id == 123
    assert summary.message_chat_id == 456
    assert summary.start_payload is None
    assert summary.parsed_start_payload is None
    assert summary.telegram_user is None


def test_summarize_update_rejects_missing_update_id() -> None:
    with pytest.raises(TelegramUpdateError, match="update_id"):
        summarize_update({"message": {"text": "/start"}})


def test_aiogram_dispatcher_factory_returns_dispatcher() -> None:
    dispatcher = create_dispatcher()

    assert dispatcher is not None
