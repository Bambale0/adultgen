"""Admin API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class AdminUserResponse(BaseModel):
    """User summary for admin dashboards."""

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
    created_at: datetime
    updated_at: datetime


class AdminUserListResponse(BaseModel):
    """Paginated admin user list."""

    items: list[AdminUserResponse]


class AdminUserFlagsPatchRequest(BaseModel):
    """Admin user capability patch."""

    is_blocked: bool | None = None
    can_generate: bool | None = None
    can_publish_profile: bool | None = None
    can_publish_feed: bool | None = None
    can_use_payments: bool | None = None
    reason: str = Field(min_length=3, max_length=500)
    admin_user_id: uuid.UUID | None = None


class AdminGenerationResponse(BaseModel):
    """Generation task summary for admin dashboards."""

    id: uuid.UUID
    user_id: uuid.UUID
    provider: str
    model_code: str
    operation: str
    status: str
    provider_task_id: str | None
    reserved_credits: int
    charged_credits: int
    error_code: str | None
    error_message: str | None
    created_at: datetime
    submitted_at: datetime | None
    completed_at: datetime | None


class AdminGenerationListResponse(BaseModel):
    """Admin generation task list."""

    items: list[AdminGenerationResponse]


class AdminPublicationResponse(BaseModel):
    """Publication summary for admin dashboards."""

    id: uuid.UUID
    user_id: uuid.UUID
    asset_id: uuid.UUID
    title: str | None
    visibility: str
    is_explicit: bool
    blur_required: bool
    status: str
    published_at: datetime
    deleted_at: datetime | None


class AdminPublicationListResponse(BaseModel):
    """Admin publication list."""

    items: list[AdminPublicationResponse]


class AdminPublicationStatusRequest(BaseModel):
    """Admin publication moderation status change."""

    status: str
    reason: str = Field(min_length=3, max_length=500)
    admin_user_id: uuid.UUID | None = None


class AdminPaymentOrderResponse(BaseModel):
    """Payment order summary for finance support."""

    id: uuid.UUID
    user_id: uuid.UUID
    provider: str
    package_code: str
    amount_minor: int
    currency: str
    credits_amount: int
    status: str
    external_payment_id: str | None
    provider_checkout_url: str | None
    expires_at: datetime
    paid_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AdminPaymentOrderListResponse(BaseModel):
    """Admin payment order list."""

    items: list[AdminPaymentOrderResponse]


class AdminWalletAdjustmentRequest(BaseModel):
    """Manual wallet adjustment request."""

    user_id: uuid.UUID
    amount: int
    bucket: str = "bonus"
    reason: str = Field(min_length=3, max_length=500)
    admin_user_id: uuid.UUID | None = None


class AdminWalletAdjustmentResponse(BaseModel):
    """Manual wallet adjustment result."""

    user_id: uuid.UUID
    amount: int
    bucket: str
    total_available: int
    total_reserved: int


class AdminAuditEventResponse(BaseModel):
    """Admin audit event response."""

    id: uuid.UUID
    admin_user_id: uuid.UUID | None
    target_type: str
    target_id: uuid.UUID | None
    action: str
    reason: str | None
    before_state: dict[str, object]
    after_state: dict[str, object]
    created_at: datetime


class AdminAuditEventListResponse(BaseModel):
    """Admin audit event list."""

    items: list[AdminAuditEventResponse]
