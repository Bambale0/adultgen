"""Saved collection API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class SavedPublicationResponse(BaseModel):
    """Saved publication response."""

    publication_id: uuid.UUID
    saved_at: datetime


class SavedPublicationListResponse(BaseModel):
    """Saved collection list response."""

    items: list[SavedPublicationResponse]
