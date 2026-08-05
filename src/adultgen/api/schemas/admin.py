"""Admin API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class AdminUserResponse(BaseModel):
    """Admin-facing user row."""

    id: uuid.UUID
    telegram_user_id: int
    username: str | None
    first_name: str | None
    last_name: str | None
    is_blocked: bool
    can_generate: bool
    can_publish_profile: bool
    can_publish_feed: bool
    can_use_payments: bool
    cached_available_balance: int | None = None
    cached_reserved_balance: int | None = None
    created_at: datetime
    updated_at: datetime


class AdminUserListResponse(BaseModel):
    """Paginated admin user list."""

    items: list[AdminUserResponse]


class AdminUserCapabilityUpdateRequest(BaseModel):
    """Partial user capability update."""

    is_blocked: bool | None = None
    can_generate: bool | None = None
    can_publish_profile: bool | None = None
    can_publish_feed: bool | None = None
    can_use_payments: bool | None = None
    reason: str = Field(min_length=3, max_length=500)


class AdminGenerationResponse(BaseModel):
    """Admin-facing generation task row."""

    id: uuid.UUID
    user_id: uuid.UUID
    status: str
    provider: str
    model_code: str
    operation: str
    reserved_credits: int
    charged_credits: int
    provider_task_id: str | None
    error_code: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class AdminGenerationListResponse(BaseModel):
    """Admin generation list."""

    items: list[AdminGenerationResponse]


class AdminPublicationResponse(BaseModel):
    """Admin-facing publication row."""

    id: uuid.UUID
    user_id: uuid.UUID
    asset_id: uuid.UUID
    visibility: str
    status: str
    title: str | None
    description: str | None
    is_explicit: bool
    blur_required: bool
    published_at: datetime | None
    deleted_at: datetime | None
    media_url: str


class AdminPublicationListResponse(BaseModel):
    """Admin publication list."""

    items: list[AdminPublicationResponse]


class AdminPublicationActionRequest(BaseModel):
    """Action to mutate a publication moderation state."""

    action: Literal["hide", "restore", "delete"]
    reason: str = Field(min_length=3, max_length=500)


class AdminPaymentOrderResponse(BaseModel):
    """Admin-facing payment order row."""

    id: uuid.UUID
    user_id: uuid.UUID
    provider: str
    external_payment_id: str | None
    package_code: str
    amount_minor: int
    currency: str
    credits_amount: int
    status: str
    expires_at: datetime
    paid_at: datetime | None
    provider_checkout_url: str | None
    created_at: datetime
    updated_at: datetime


class AdminPaymentOrderListResponse(BaseModel):
    """Admin payment order list."""

    items: list[AdminPaymentOrderResponse]


class AdminWalletAdjustmentRequest(BaseModel):
    """Append an admin wallet adjustment."""

    user_id: uuid.UUID
    amount: int = Field(ge=1, le=1_000_000)
    bucket: Literal["purchased", "subscription", "bonus"] = "bonus"
    reason: str = Field(min_length=3, max_length=500)
    admin_user_id: uuid.UUID | None = None


class AdminWalletAdjustmentResponse(BaseModel):
    """Wallet state after an admin adjustment."""

    user_id: uuid.UUID
    operation_id: uuid.UUID
    amount: int
    bucket: str
    total_available: int
    total_reserved: int


class AdminAuditEventResponse(BaseModel):
    """Admin audit event row."""

    id: uuid.UUID
    admin_user_id: uuid.UUID | None
    target_type: str
    target_id: uuid.UUID | None
    action: str
    reason: str | None
    before_state: dict[str, Any]
    after_state: dict[str, Any]
    created_at: datetime


class AdminAuditEventListResponse(BaseModel):
    """Admin audit event list."""

    items: list[AdminAuditEventResponse]
