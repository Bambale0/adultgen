import pytest

from adultgen.telegram_gateway.start_payload import (
    StartPayloadError,
    StartPayloadKind,
    parse_start_payload,
)


def test_parse_empty_start_payload_returns_none() -> None:
    assert parse_start_payload(None) is None
    assert parse_start_payload(" ") is None


def test_parse_profile_start_payload() -> None:
    parsed = parse_start_payload("profile_a8Pk3mQ")

    assert parsed is not None
    assert parsed.kind == StartPayloadKind.PROFILE
    assert parsed.raw == "profile_a8Pk3mQ"
    assert parsed.profile_public_id == "a8Pk3mQ"
    assert parsed.referral_code is None


def test_parse_referral_start_payload() -> None:
    parsed = parse_start_payload("ref_partner-42")

    assert parsed is not None
    assert parsed.kind == StartPayloadKind.REFERRAL
    assert parsed.raw == "ref_partner-42"
    assert parsed.profile_public_id is None
    assert parsed.referral_code == "partner-42"


def test_rejects_unknown_start_payload_kind() -> None:
    with pytest.raises(StartPayloadError, match="Unsupported"):
        parse_start_payload("unknown_abc123")


def test_rejects_unsafe_start_payload_characters() -> None:
    with pytest.raises(StartPayloadError, match="unsupported characters"):
        parse_start_payload("profile_abc<script>")


def test_rejects_too_short_profile_public_id() -> None:
    with pytest.raises(StartPayloadError, match="Profile public id"):
        parse_start_payload("profile_abc")
