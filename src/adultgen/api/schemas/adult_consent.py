"""Adult consent API schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AdultConsentStatusResponse(BaseModel):
    """Adult policy acceptance status."""

    accepted: bool
    policy_version: str
    accepted_at: datetime | None = None


class AdultConsentAcceptResponse(BaseModel):
    """Adult policy acceptance response."""

    accepted: bool
    policy_version: str
    accepted_at: datetime
