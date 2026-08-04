"""Notification delivery retry policy."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


class DeliveryRetryError(ValueError):
    """Raised when retry policy input is invalid."""


@dataclass(frozen=True, slots=True)
class DeliveryRetryDecision:
    """Retry decision after a failed delivery attempt."""

    should_retry: bool
    attempts: int
    next_retry_at: datetime | None


def decide_delivery_retry(
    *,
    previous_attempts: int,
    now: datetime,
    max_attempts: int = 3,
    base_delay_seconds: int = 60,
) -> DeliveryRetryDecision:
    """Return retry decision with exponential backoff.

    `previous_attempts` is the number already persisted before the current
    failure. The returned `attempts` includes the current failed attempt.
    """

    if previous_attempts < 0:
        raise DeliveryRetryError("previous_attempts cannot be negative.")
    if max_attempts <= 0:
        raise DeliveryRetryError("max_attempts must be positive.")
    if base_delay_seconds <= 0:
        raise DeliveryRetryError("base_delay_seconds must be positive.")

    attempts = previous_attempts + 1
    if attempts >= max_attempts:
        return DeliveryRetryDecision(
            should_retry=False,
            attempts=attempts,
            next_retry_at=None,
        )

    delay_seconds = base_delay_seconds * (2 ** (attempts - 1))
    return DeliveryRetryDecision(
        should_retry=True,
        attempts=attempts,
        next_retry_at=now + timedelta(seconds=delay_seconds),
    )
