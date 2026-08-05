"""Billing application service for credit purchases."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.config import Settings
from adultgen.db.models.payments import PaymentOrder
from adultgen.domain.credit_packages import CreditPackage, CreditPackageError, get_credit_package
from adultgen.domain.enums import CreditBucket, PaymentOrderStatus, PaymentProviderCode, WalletEntryType
from adultgen.integrations.payments.crocopay import CrocoPayCheckout
from adultgen.services.wallets import credit_wallet


class BillingServiceError(ValueError):
    """Raised when billing state cannot be changed safely."""


@dataclass(frozen=True, slots=True)
class CreatedPaymentOrder:
    """A payment order plus one-time checkout/callback URLs."""

    order: PaymentOrder
    package: CreditPackage
    checkout_url: str
    callback_url: str


@dataclass(frozen=True, slots=True)
class PaidPaymentOrderResult:
    """Result of idempotent successful-payment processing."""

    order: PaymentOrder
    credited_now: bool


async def create_payment_order(
    session: AsyncSession,
    *,
    settings: Settings,
    user_id: uuid.UUID,
    package_code: str,
    provider: PaymentProviderCode,
    now: datetime | None = None,
    expires_in: timedelta = timedelta(minutes=30),
) -> CreatedPaymentOrder:
    """Create an internal payment order before redirecting to a provider checkout."""

    package = get_credit_package(package_code)
    resolved_now = now or datetime.now(UTC)
    checkout_token = secrets.token_urlsafe(32)
    callback_token = secrets.token_urlsafe(32)
    checkout_url = f"{settings.billing_base_url.rstrip('/')}/checkout/{checkout_token}"
    callback_url = f"{settings.billing_base_url.rstrip('/')}/webhooks/payments/{provider.value}?token={callback_token}"
    order = PaymentOrder(
        user_id=user_id,
        provider=provider.value,
        checkout_token_hash=hash_billing_token(checkout_token),
        callback_token_hash=hash_billing_token(callback_token),
        package_code=package.code,
        amount_minor=package.amount_minor,
        currency=package.currency,
        credits_amount=package.credits,
        status=PaymentOrderStatus.CREATED.value,
        expires_at=resolved_now + expires_in,
    )
    session.add(order)
    await session.flush()
    return CreatedPaymentOrder(order=order, package=package, checkout_url=checkout_url, callback_url=callback_url)


async def attach_provider_checkout(
    session: AsyncSession,
    *,
    order_id: uuid.UUID,
    checkout: CrocoPayCheckout,
) -> PaymentOrder:
    """Attach provider checkout URL/external id after successful provider initiation."""

    order = await get_payment_order_for_update(session, order_id)
    if PaymentOrderStatus(order.status) not in {PaymentOrderStatus.CREATED, PaymentOrderStatus.PENDING}:
        raise BillingServiceError("Payment order cannot be redirected in its current status.")
    order.external_payment_id = checkout.external_payment_id
    order.provider_checkout_url = checkout.redirect_url
    order.status = PaymentOrderStatus.REDIRECTED.value
    await session.flush()
    return order


async def mark_payment_order_paid_by_callback_token(
    session: AsyncSession,
    *,
    callback_token: str,
    provider: PaymentProviderCode,
    amount_minor: int,
    signature_valid: bool,
    now: datetime | None = None,
) -> PaidPaymentOrderResult:
    """Mark a payment order as paid by one-time callback token."""

    order = await get_payment_order_by_callback_token(session, callback_token=callback_token, provider=provider)
    return await _mark_payment_order_paid(
        session,
        order=order,
        amount_minor=amount_minor,
        signature_valid=signature_valid,
        now=now,
    )


async def mark_payment_order_paid_by_id(
    session: AsyncSession,
    *,
    order_id: uuid.UUID,
    provider: PaymentProviderCode,
    amount_minor: int,
    signature_valid: bool,
    now: datetime | None = None,
) -> PaidPaymentOrderResult:
    """Mark a payment order as paid by order id from provider callback URL."""

    order = await get_payment_order_for_update(session, order_id)
    if order.provider != provider.value:
        raise BillingServiceError("Payment order provider does not match callback provider.")
    return await _mark_payment_order_paid(
        session,
        order=order,
        amount_minor=amount_minor,
        signature_valid=signature_valid,
        now=now,
    )


async def _mark_payment_order_paid(
    session: AsyncSession,
    *,
    order: PaymentOrder,
    amount_minor: int,
    signature_valid: bool,
    now: datetime | None,
) -> PaidPaymentOrderResult:
    if not signature_valid:
        raise BillingServiceError("Payment callback signature is invalid.")

    current_status = PaymentOrderStatus(order.status)
    if current_status == PaymentOrderStatus.PAID:
        return PaidPaymentOrderResult(order=order, credited_now=False)
    if current_status in {
        PaymentOrderStatus.FAILED,
        PaymentOrderStatus.CANCELLED,
        PaymentOrderStatus.REFUNDED,
        PaymentOrderStatus.CHARGEBACK,
    }:
        raise BillingServiceError("Payment order is terminal and cannot be paid.")
    if amount_minor != order.amount_minor:
        raise BillingServiceError("Payment callback amount does not match order amount.")

    order.status = PaymentOrderStatus.PAID.value
    order.paid_at = now or datetime.now(UTC)
    await credit_wallet(
        session,
        user_id=order.user_id,
        amount=order.credits_amount,
        bucket=CreditBucket.PURCHASED,
        entry_type=WalletEntryType.PAYMENT_CREDIT,
        operation_id=order.id,
        payment_order_id=order.id,
        reason=f"Payment order {order.id} credited.",
    )
    await session.flush()
    return PaidPaymentOrderResult(order=order, credited_now=True)


async def get_payment_order_for_update(session: AsyncSession, order_id: uuid.UUID) -> PaymentOrder:
    """Return a locked payment order by id."""

    result = await session.execute(select(PaymentOrder).where(PaymentOrder.id == order_id).with_for_update())
    order = result.scalar_one_or_none()
    if order is None:
        raise BillingServiceError("Payment order not found.")
    return order


async def get_payment_order_by_callback_token(
    session: AsyncSession,
    *,
    callback_token: str,
    provider: PaymentProviderCode,
) -> PaymentOrder:
    """Return a locked payment order by raw callback token."""

    token_hash = hash_billing_token(callback_token)
    result = await session.execute(
        select(PaymentOrder)
        .where(PaymentOrder.provider == provider.value, PaymentOrder.callback_token_hash == token_hash)
        .with_for_update()
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise BillingServiceError("Payment order not found for callback token.")
    return order


def hash_billing_token(token: str) -> str:
    """Hash one-time checkout/callback tokens before persistence."""

    if not token:
        raise BillingServiceError("Billing token cannot be empty.")
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def package_or_422(package_code: str) -> CreditPackage:
    """Return package or normalize package catalog errors for API callers."""

    try:
        return get_credit_package(package_code)
    except CreditPackageError as exc:
        raise BillingServiceError(str(exc)) from exc
