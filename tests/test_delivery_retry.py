from datetime import UTC, datetime, timedelta

import pytest

from adultgen.domain.delivery_retry import DeliveryRetryError, decide_delivery_retry


def test_delivery_retry_schedules_exponential_backoff() -> None:
    now = datetime(2026, 8, 5, 0, 0, tzinfo=UTC)

    first = decide_delivery_retry(previous_attempts=0, now=now)
    second = decide_delivery_retry(previous_attempts=1, now=now)

    assert first.should_retry is True
    assert first.attempts == 1
    assert first.next_retry_at == now + timedelta(seconds=60)

    assert second.should_retry is True
    assert second.attempts == 2
    assert second.next_retry_at == now + timedelta(seconds=120)


def test_delivery_retry_stops_at_max_attempts() -> None:
    now = datetime(2026, 8, 5, 0, 0, tzinfo=UTC)

    decision = decide_delivery_retry(previous_attempts=2, now=now, max_attempts=3)

    assert decision.should_retry is False
    assert decision.attempts == 3
    assert decision.next_retry_at is None


def test_delivery_retry_rejects_invalid_inputs() -> None:
    now = datetime(2026, 8, 5, 0, 0, tzinfo=UTC)

    with pytest.raises(DeliveryRetryError, match="negative"):
        decide_delivery_retry(previous_attempts=-1, now=now)

    with pytest.raises(DeliveryRetryError, match="max_attempts"):
        decide_delivery_retry(previous_attempts=0, now=now, max_attempts=0)

    with pytest.raises(DeliveryRetryError, match="base_delay"):
        decide_delivery_retry(previous_attempts=0, now=now, base_delay_seconds=0)
