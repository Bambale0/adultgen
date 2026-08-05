"""Website billing API routes."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.api.dependencies import get_current_token_claims, get_db_session, get_runtime_settings
from adultgen.api.schemas.billing import (
    CreatePaymentOrderRequest,
    CreditPackageListResponse,
    CreditPackageResponse,
    InitiateProviderCheckoutResponse,
    PaymentOrderResponse,
)
from adultgen.config import Settings
from adultgen.domain.credit_packages import list_credit_packages
from adultgen.domain.enums import PaymentProviderCode
from adultgen.integrations.payments.crocopay import (
    CrocoPayError,
    CrocoPayInitiatePaymentCommand,
    initiate_crocopay_payment,
)
from adultgen.security.tokens import AccessTokenClaims
from adultgen.services.billing import (
    BillingServiceError,
    attach_provider_checkout,
    create_payment_order,
    get_payment_order_for_update,
)

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/packages", response_model=CreditPackageListResponse)
async def get_credit_packages() -> CreditPackageListResponse:
    """Return enabled credit packages for the website billing page."""

    return CreditPackageListResponse(items=[_package_response(package) for package in list_credit_packages()])


@router.post("/orders", response_model=PaymentOrderResponse, status_code=status.HTTP_201_CREATED)
async def create_billing_order(
    payload: CreatePaymentOrderRequest,
    claims: Annotated[AccessTokenClaims, Depends(get_current_token_claims)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_runtime_settings)],
) -> PaymentOrderResponse:
    """Create an internal payment order and one-time checkout/callback URLs."""

    try:
        created = await create_payment_order(
            session,
            settings=settings,
            user_id=claims.subject,
            package_code=payload.package_code,
            provider=payload.provider,
        )
    except BillingServiceError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    return _order_response(created.order, checkout_url=created.checkout_url, callback_url=created.callback_url)


@router.post("/orders/{order_id}/crocopay", response_model=InitiateProviderCheckoutResponse)
async def initiate_crocopay_checkout(
    order_id: uuid.UUID,
    claims: Annotated[AccessTokenClaims, Depends(get_current_token_claims)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_runtime_settings)],
) -> InitiateProviderCheckoutResponse:
    """Create a CrocoPay checkout link for an owned order."""

    try:
        order = await get_payment_order_for_update(session, order_id)
    except BillingServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    if order.user_id != claims.subject:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Payment order is not owned by user.")
    if order.provider != PaymentProviderCode.CROCOPAY.value:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Payment order provider is not CrocoPay.",
        )

    client_id = settings.crocopay_client_id or settings.crocopay_api_key
    client_secret = settings.crocopay_client_secret or settings.crocopay_secret
    if not client_id or not client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CrocoPay credentials are not configured.",
        )

    base_url = settings.billing_base_url.rstrip("/")
    try:
        checkout = await initiate_crocopay_payment(
            api_base_url=settings.crocopay_api_base_url,
            command=CrocoPayInitiatePaymentCommand(
                client_id=client_id,
                client_secret=client_secret,
                amount_minor=order.amount_minor,
                currency=order.currency,
                success_url=f"{base_url}/billing/success?order_id={order.id}",
                cancel_url=f"{base_url}/billing/cancel?order_id={order.id}",
                callback_url=f"{base_url}/webhooks/payments/crocopay?order_id={order.id}",
            ),
        )
        updated_order = await attach_provider_checkout(session, order_id=order.id, checkout=checkout)
    except (BillingServiceError, CrocoPayError) as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    return InitiateProviderCheckoutResponse(order=_order_response(updated_order), redirect_url=checkout.redirect_url)


def _package_response(package: object) -> CreditPackageResponse:
    return CreditPackageResponse(
        code=package.code,
        title=package.title,
        credits=package.credits,
        amount_minor=package.amount_minor,
        amount_major=package.amount_major,
        currency=package.currency,
        description=package.description,
        is_popular=package.is_popular,
    )


def _order_response(
    order: object,
    *,
    checkout_url: str | None = None,
    callback_url: str | None = None,
) -> PaymentOrderResponse:
    return PaymentOrderResponse(
        id=order.id,
        provider=order.provider,
        package_code=order.package_code,
        amount_minor=order.amount_minor,
        currency=order.currency,
        credits_amount=order.credits_amount,
        status=order.status,
        expires_at=order.expires_at,
        paid_at=order.paid_at,
        checkout_url=checkout_url,
        callback_url=callback_url,
        provider_checkout_url=order.provider_checkout_url,
        external_payment_id=order.external_payment_id,
    )
