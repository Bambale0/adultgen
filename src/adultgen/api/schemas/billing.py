"""Billing API schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from adultgen.domain.enums import PaymentProviderCode


class CreditPackageResponse(BaseModel):
    """Credit package exposed to the website billing page."""

    code: str
    title: str
    credits: int
    amount_minor: int
    amount_major: str
    currency: str
    description: str
    is_popular: bool


class CreditPackageListResponse(BaseModel):
    """List of enabled credit packages."""

    items: list[CreditPackageResponse]


class CreatePaymentOrderRequest(BaseModel):
    """Create a payment order for a package/provider pair."""

    package_code: str
    provider: PaymentProviderCode = PaymentProviderCode.CROCOPAY


class PaymentOrderResponse(BaseModel):
    """Payment order state returned to API clients."""

    id: uuid.UUID
    provider: str
    package_code: str
    amount_minor: int
    currency: str
    credits_amount: int
    status: str
    expires_at: datetime
    paid_at: datetime | None
    checkout_url: str | None = None
    callback_url: str | None = None
    provider_checkout_url: str | None = None
    external_payment_id: str | None = None


class InitiateProviderCheckoutResponse(BaseModel):
    """Provider checkout URL for browser redirect."""

    order: PaymentOrderResponse
    redirect_url: str


class PaymentWebhookResponse(BaseModel):
    """Payment webhook processing response."""

    provider: str
    payment_order_id: uuid.UUID | None
    status: str
    credited_now: bool
    signature_valid: bool
