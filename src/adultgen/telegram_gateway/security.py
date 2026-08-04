"""Telegram webhook security helpers."""

from __future__ import annotations

import hashlib
import hmac


class TelegramWebhookSecurityError(ValueError):
    """Raised when Telegram webhook authentication fails."""


def hash_webhook_secret(secret: str) -> str:
    """Return a stable SHA-256 hash for a webhook secret token."""

    if not secret:
        raise TelegramWebhookSecurityError("Webhook secret cannot be empty.")
    return hashlib.sha256(secret.encode()).hexdigest()


def verify_webhook_secret(*, provided_secret: str | None, expected_hash: str) -> None:
    """Verify Telegram secret token header against stored hash."""

    if not provided_secret:
        raise TelegramWebhookSecurityError("Missing Telegram webhook secret token.")
    if not expected_hash:
        raise TelegramWebhookSecurityError("Stored Telegram webhook secret hash is empty.")

    provided_hash = hash_webhook_secret(provided_secret)
    if not hmac.compare_digest(provided_hash, expected_hash):
        raise TelegramWebhookSecurityError("Invalid Telegram webhook secret token.")
