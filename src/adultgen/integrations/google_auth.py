"""Google Identity Services server-side token verification."""

from __future__ import annotations

from dataclasses import dataclass

from anyio import to_thread
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests
from google.oauth2 import id_token


class GoogleIdentityError(ValueError):
    """Raised when a Google ID token cannot establish a trusted identity."""


@dataclass(frozen=True, slots=True)
class GoogleIdentity:
    """Verified subset of Google identity claims used by AdultGen."""

    subject: str
    email: str
    display_name: str


async def verify_google_identity_token(credential: str, *, client_id: str) -> GoogleIdentity:
    """Verify signature, issuer, expiry, audience, and required account claims."""

    if not client_id:
        raise GoogleIdentityError("Google authentication is not configured.")

    def verify() -> dict[str, object]:
        return id_token.verify_oauth2_token(credential, requests.Request(), client_id)

    try:
        claims = await to_thread.run_sync(verify)
    except (GoogleAuthError, ValueError) as exc:
        raise GoogleIdentityError("Google credential is invalid or expired.") from exc

    subject = str(claims.get("sub") or "").strip()
    email = str(claims.get("email") or "").strip().lower()
    display_name = str(claims.get("name") or claims.get("given_name") or "").strip()
    if not subject or not email or claims.get("email_verified") is not True:
        raise GoogleIdentityError("Google account must provide a verified email address.")

    return GoogleIdentity(
        subject=subject,
        email=email,
        display_name=(display_name or email.split("@", maxsplit=1)[0])[:120],
    )
