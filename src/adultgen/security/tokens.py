"""Small signed access-token helper.

The project can later switch to a full JWT library without changing API/router code.
For the MVP foundation we keep a compact HMAC-SHA256 token with JWT-like parts.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import uuid
from dataclasses import dataclass
from typing import Any


class TokenError(ValueError):
    """Raised when an access token cannot be created or verified."""


@dataclass(frozen=True, slots=True)
class AccessTokenClaims:
    """Claims stored inside an AdultGen access token."""

    subject: uuid.UUID
    telegram_user_id: int
    issued_at: int
    expires_at: int


def create_access_token(
    *,
    subject: uuid.UUID,
    telegram_user_id: int,
    secret: str,
    ttl_seconds: int,
    now_ts: int | None = None,
) -> str:
    """Create a compact HMAC-signed token for Core API calls."""

    if ttl_seconds <= 0:
        raise TokenError("Token ttl_seconds must be positive.")

    issued_at = int(now_ts or time.time())
    payload = {
        "sub": str(subject),
        "telegram_user_id": telegram_user_id,
        "iat": issued_at,
        "exp": issued_at + ttl_seconds,
    }
    header = {"alg": "HS256", "typ": "JWT"}

    encoded_header = _b64url_json(header)
    encoded_payload = _b64url_json(payload)
    signature = _sign(f"{encoded_header}.{encoded_payload}", secret)
    return f"{encoded_header}.{encoded_payload}.{signature}"


def verify_access_token(token: str, *, secret: str, now_ts: int | None = None) -> AccessTokenClaims:
    """Verify token signature and return typed claims."""

    parts = token.split(".")
    if len(parts) != 3:
        raise TokenError("Token must contain three dot-separated parts.")

    encoded_header, encoded_payload, signature = parts
    expected_signature = _sign(f"{encoded_header}.{encoded_payload}", secret)
    if not hmac.compare_digest(signature, expected_signature):
        raise TokenError("Invalid token signature.")

    header = _decode_json(encoded_header)
    if header.get("alg") != "HS256":
        raise TokenError("Unsupported token algorithm.")

    payload = _decode_json(encoded_payload)
    expires_at = int(payload["exp"])
    if int(now_ts or time.time()) > expires_at:
        raise TokenError("Token expired.")

    return AccessTokenClaims(
        subject=uuid.UUID(str(payload["sub"])),
        telegram_user_id=int(payload["telegram_user_id"]),
        issued_at=int(payload["iat"]),
        expires_at=expires_at,
    )


def _sign(message: str, secret: str) -> str:
    digest = hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest()
    return _b64url_bytes(digest)


def _b64url_json(value: dict[str, Any]) -> str:
    raw = json.dumps(value, separators=(",", ":"), sort_keys=True).encode()
    return _b64url_bytes(raw)


def _b64url_bytes(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def _decode_json(encoded: str) -> dict[str, Any]:
    padding = "=" * (-len(encoded) % 4)
    try:
        decoded = base64.urlsafe_b64decode(f"{encoded}{padding}")
        value = json.loads(decoded)
    except (ValueError, TypeError) as exc:
        raise TokenError("Invalid token JSON payload.") from exc

    if not isinstance(value, dict):
        raise TokenError("Token JSON payload must be an object.")
    return value
