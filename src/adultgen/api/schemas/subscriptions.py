"""Subscription API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class SubscriptionPlanResponse(BaseModel):
    """Subscription plan exposed to the website."""

    code: str
    title: str
    credits_per_period: int
    amount_minor: int
    amount_major: str
    currency: str
    period_days: int
    rollover_policy: str
    description: str
    is_popular: bool


class SubscriptionPlanListResponse(BaseModel):
    """List of enabled subscription plans."""

    items: list[SubscriptionPlanResponse]


class ActivateSubscriptionRequest(BaseModel):
    """Activate an MVP subscription plan."""

    plan_code: str
    provider: str | None = None
    provider_subscription_id: str | None = None


class SubscriptionResponse(BaseModel):
    """User subscription state."""

    id: uuid.UUID
    plan_code: str
    status: str
    provider: str | None
    provider_subscription_id: str | None
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    cancelled_at: datetime | None
    last_granted_at: datetime | None


class SubscriptionActivationResponse(BaseModel):
    """Activation response with grant info."""

    subscription: SubscriptionResponse
    plan: SubscriptionPlanResponse
    granted_now: bool
    grant_id: uuid.UUID | None
    credits_granted: int
