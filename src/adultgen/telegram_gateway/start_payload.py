"""Telegram /start payload parser.

Start payloads must stay short, opaque, and safe to expose in public links.
Never put Telegram user ids or internal UUIDs into these payloads.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

_SAFE_PAYLOAD_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_PUBLIC_ID_RE = re.compile(r"^[A-Za-z0-9_-]{4,32}$")
_REFERRAL_CODE_RE = re.compile(r"^[A-Za-z0-9_-]{4,48}$")


class StartPayloadError(ValueError):
    """Raised when /start payload is malformed."""


class StartPayloadKind(StrEnum):
    """Supported Telegram /start payload kinds."""

    PROFILE = "profile"
    REFERRAL = "referral"


@dataclass(frozen=True, slots=True)
class StartPayload:
    """Typed parsed Telegram /start payload."""

    kind: StartPayloadKind
    raw: str
    profile_public_id: str | None = None
    referral_code: str | None = None


def parse_start_payload(raw: str | None) -> StartPayload | None:
    """Parse optional Telegram /start payload into a typed value."""

    if raw is None:
        return None

    payload = raw.strip()
    if not payload:
        return None
    if not _SAFE_PAYLOAD_RE.fullmatch(payload):
        raise StartPayloadError("Start payload contains unsupported characters.")

    if payload.startswith("profile_"):
        public_id = payload.removeprefix("profile_")
        if not _PUBLIC_ID_RE.fullmatch(public_id):
            raise StartPayloadError("Profile public id is invalid.")
        return StartPayload(
            kind=StartPayloadKind.PROFILE,
            raw=payload,
            profile_public_id=public_id,
        )

    if payload.startswith("ref_"):
        referral_code = payload.removeprefix("ref_")
        if not _REFERRAL_CODE_RE.fullmatch(referral_code):
            raise StartPayloadError("Referral code is invalid.")
        return StartPayload(
            kind=StartPayloadKind.REFERRAL,
            raw=payload,
            referral_code=referral_code,
        )

    raise StartPayloadError("Unsupported start payload kind.")
