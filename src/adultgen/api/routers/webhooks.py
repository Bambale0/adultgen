"""Provider webhook routes."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.api.dependencies import get_db_session, get_runtime_settings
from adultgen.api.schemas.billing import PaymentWebhookResponse
from adultgen.api.schemas.webhooks import KieCallbackResponse
from adultgen.config import Settings
from adultgen.db.models.payments import PaymentWebhookProcessing, PaymentWebhookRaw
from adultgen.domain.enums import PaymentProviderCode
from adultgen.integrations.payments.crocopay import CrocoPayError, verify_crocopay_callback
from adultgen.services.billing import (
    BillingServiceError,
    mark_payment_order_paid_by_callback_token,
    mark_payment_order_paid_by_id,
)
from adultgen.services.kie_callbacks import KieCallbackError, ingest_kie_callback

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/kie", response_model=KieCallbackResponse)
async def ingest_kie_provider_callback(
    payload: dict[str, object],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_runtime_settings)],
    secret: Annotated[str | None, Query()] = None,
    x_adultgen_webhook_secret: Annotated[str | None, Header(alias="X-AdultGen-Webhook-Secret")] = None,
) -> KieCallbackResponse:
    """Ingest Kie task completion/failure callbacks.

    The callback URL can include `?secret=...`; a custom header is also accepted
    for providers or reverse proxies that support it.
    """

    configured_secret = settings.kie_webhook_secret.strip()
    if configured_secret:
        received_secret = secret or x_adultgen_webhook_secret
        if received_secret != configured_secret:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Kie webhook secret.")

    try:
        result = await ingest_kie_callback(session, settings=settings, payload=payload)
    except KieCallbackError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    return KieCallbackResponse(
        provider_task_id=result.provider_task_id,
        generation_task_id=result.generation_task_id,
        status=result.status,
        changed_task=result.changed_task,
        result_asset_ids=list(result.result_asset_ids),
        scene_take_id=result.scene_take_id,
    )


@router.post("/payments/crocopay", response_model=PaymentWebhookResponse)
async def ingest_crocopay_payment_webhook(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db_session)],
    settings: Annotated[Settings, Depends(get_runtime_settings)],
    token: Annotated[str | None, Query()] = None,
    order_id: Annotated[uuid.UUID | None, Query()] = None,
) -> PaymentWebhookResponse:
    """Ingest a successful CrocoPay callback and credit purchased credits."""

    raw_body = await request.body()
    payload = _json_body(raw_body)
    client_secret = settings.crocopay_client_secret or settings.crocopay_secret
    if not client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CrocoPay secret is not configured.",
        )

    try:
        parsed = verify_crocopay_callback(payload, client_secret=client_secret)
    except CrocoPayError as exc:
        await _record_payment_webhook(
            session,
            provider=PaymentProviderCode.CROCOPAY,
            request=request,
            raw_body=raw_body,
            signature_valid=False,
            status_value="failed",
            last_error=str(exc),
        )
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    raw = await _record_payment_webhook(
        session,
        provider=PaymentProviderCode.CROCOPAY,
        request=request,
        raw_body=raw_body,
        signature_valid=parsed.signature_valid,
        status_value="received",
        last_error=None,
    )

    if not token and not order_id:
        raw_processing = PaymentWebhookProcessing(
            webhook_raw_id=raw.id,
            status="failed",
            attempt_count=1,
            last_error="CrocoPay callback is missing token or order_id.",
            processed_at=datetime.now(UTC),
        )
        session.add(raw_processing)
        await session.flush()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Callback is missing token or order_id.",
        )

    try:
        if token:
            result = await mark_payment_order_paid_by_callback_token(
                session,
                callback_token=token,
                provider=PaymentProviderCode.CROCOPAY,
                amount_minor=parsed.subtotal,
                signature_valid=parsed.signature_valid,
            )
        else:
            assert order_id is not None
            result = await mark_payment_order_paid_by_id(
                session,
                order_id=order_id,
                provider=PaymentProviderCode.CROCOPAY,
                amount_minor=parsed.subtotal,
                signature_valid=parsed.signature_valid,
            )
    except BillingServiceError as exc:
        session.add(
            PaymentWebhookProcessing(
                webhook_raw_id=raw.id,
                status="failed",
                attempt_count=1,
                last_error=str(exc),
                processed_at=datetime.now(UTC),
            )
        )
        await session.flush()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    session.add(
        PaymentWebhookProcessing(
            webhook_raw_id=raw.id,
            status="processed",
            attempt_count=1,
            payment_order_id=result.order.id,
            processed_at=datetime.now(UTC),
        )
    )
    await session.flush()
    return PaymentWebhookResponse(
        provider=PaymentProviderCode.CROCOPAY.value,
        payment_order_id=result.order.id,
        status=result.order.status,
        credited_now=result.credited_now,
        signature_valid=parsed.signature_valid,
    )


async def _record_payment_webhook(
    session: AsyncSession,
    *,
    provider: PaymentProviderCode,
    request: Request,
    raw_body: bytes,
    signature_valid: bool | None,
    status_value: str,
    last_error: str | None,
) -> PaymentWebhookRaw:
    received_at = datetime.now(UTC)
    body_sha256 = hashlib.sha256(raw_body).hexdigest()
    event_hash = hashlib.sha256(
        f"{provider.value}|{request.url.query}|{body_sha256}|{received_at.isoformat()}".encode()
    ).hexdigest()
    raw = PaymentWebhookRaw(
        provider=provider.value,
        received_at=received_at,
        request_method=request.method,
        request_path=request.url.path,
        query_string=request.url.query,
        headers=dict(request.headers.items()),
        raw_body=raw_body,
        source_ip=request.client.host if request.client else None,
        body_sha256=body_sha256,
        signature_valid=signature_valid,
        event_hash=event_hash,
    )
    session.add(raw)
    await session.flush()
    if status_value == "failed":
        session.add(
            PaymentWebhookProcessing(
                webhook_raw_id=raw.id,
                status="failed",
                attempt_count=1,
                last_error=last_error,
                processed_at=received_at,
            )
        )
        await session.flush()
    return raw


def _json_body(raw_body: bytes) -> dict[str, Any]:
    try:
        parsed = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Webhook body must be JSON.",
        ) from exc
    if not isinstance(parsed, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Webhook JSON body must be an object.",
        )
    return parsed
