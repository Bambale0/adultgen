"""Admin API routes."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.api.dependencies import get_db_session, require_admin_api_token
from adultgen.api.schemas.admin import (
    AdminAuditEventListResponse,
    AdminAuditEventResponse,
    AdminGenerationListResponse,
    AdminGenerationResponse,
    AdminPaymentOrderListResponse,
    AdminPaymentOrderResponse,
    AdminPublicationActionRequest,
    AdminPublicationListResponse,
    AdminPublicationResponse,
    AdminUserCapabilityUpdateRequest,
    AdminUserListResponse,
    AdminUserResponse,
    AdminWalletAdjustmentRequest,
    AdminWalletAdjustmentResponse,
)
from adultgen.db.models.wallets import Wallet
from adultgen.domain.enums import CreditBucket
from adultgen.services.admin import (
    AdminServiceError,
    adjust_user_wallet,
    apply_publication_admin_action,
    list_admin_audit_events,
    list_admin_generations,
    list_admin_payment_orders,
    list_admin_publications,
    list_admin_users,
    update_user_capabilities,
)

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin_api_token)],
)


@router.get("/health")
async def admin_health(_admin: Annotated[None, Depends(require_admin_api_token)]) -> dict[str, str]:
    """Protected admin health endpoint used to verify admin auth wiring."""

    return {"status": "ok", "scope": "admin"}


@router.get("/users", response_model=AdminUserListResponse)
async def admin_list_users(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    blocked: bool | None = None,
) -> AdminUserListResponse:
    """List users with cached wallet projections."""

    try:
        users = await list_admin_users(session, limit=limit, blocked=blocked)
    except AdminServiceError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    wallet_map = await _wallets_by_user_id(session, [user.id for user in users])
    return AdminUserListResponse(
        items=[_admin_user_response(user, wallet_map.get(user.id)) for user in users]
    )


@router.patch("/users/{user_id}/capabilities", response_model=AdminUserResponse)
async def admin_update_user_capabilities(
    user_id: uuid.UUID,
    payload: AdminUserCapabilityUpdateRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AdminUserResponse:
    """Update user capability flags and audit the change."""

    try:
        user = await update_user_capabilities(
            session,
            user_id=user_id,
            reason=payload.reason,
            is_blocked=payload.is_blocked,
            can_generate=payload.can_generate,
            can_publish_profile=payload.can_publish_profile,
            can_publish_feed=payload.can_publish_feed,
            can_use_payments=payload.can_use_payments,
        )
    except AdminServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    wallet_map = await _wallets_by_user_id(session, [user.id])
    return _admin_user_response(user, wallet_map.get(user.id))


@router.get("/generations", response_model=AdminGenerationListResponse)
async def admin_list_generations(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    status_filter: str | None = Query(default=None, alias="status"),
    user_id: uuid.UUID | None = None,
) -> AdminGenerationListResponse:
    """List generation tasks across users."""

    try:
        tasks = await list_admin_generations(
            session,
            limit=limit,
            status=status_filter,
            user_id=user_id,
        )
    except AdminServiceError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return AdminGenerationListResponse(items=[_admin_generation_response(task) for task in tasks])


@router.get("/publications", response_model=AdminPublicationListResponse)
async def admin_list_publications(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    status_filter: str | None = Query(default=None, alias="status"),
    visibility: str | None = None,
    user_id: uuid.UUID | None = None,
) -> AdminPublicationListResponse:
    """List publications across users."""

    try:
        publications = await list_admin_publications(
            session,
            limit=limit,
            status=status_filter,
            visibility=visibility,
            user_id=user_id,
        )
    except AdminServiceError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return AdminPublicationListResponse(
        items=[_admin_publication_response(publication) for publication in publications]
    )


@router.post("/publications/{publication_id}/actions", response_model=AdminPublicationResponse)
async def admin_apply_publication_action(
    publication_id: uuid.UUID,
    payload: AdminPublicationActionRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AdminPublicationResponse:
    """Apply hide/restore/delete action to a publication and audit it."""

    try:
        publication = await apply_publication_admin_action(
            session,
            publication_id=publication_id,
            action=payload.action,
            reason=payload.reason,
        )
    except AdminServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _admin_publication_response(publication)


@router.get("/payments/orders", response_model=AdminPaymentOrderListResponse)
async def admin_list_payment_orders(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    status_filter: str | None = Query(default=None, alias="status"),
    provider: str | None = None,
    user_id: uuid.UUID | None = None,
) -> AdminPaymentOrderListResponse:
    """List payment orders across users."""

    try:
        orders = await list_admin_payment_orders(
            session,
            limit=limit,
            status=status_filter,
            provider=provider,
            user_id=user_id,
        )
    except AdminServiceError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return AdminPaymentOrderListResponse(items=[_admin_payment_order_response(order) for order in orders])


@router.post("/wallet/adjustments", response_model=AdminWalletAdjustmentResponse)
async def admin_adjust_wallet(
    payload: AdminWalletAdjustmentRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AdminWalletAdjustmentResponse:
    """Credit a user wallet through the ledger and audit the adjustment."""

    try:
        operation_id, balances = await adjust_user_wallet(
            session,
            user_id=payload.user_id,
            amount=payload.amount,
            bucket=CreditBucket(payload.bucket),
            reason=payload.reason,
            admin_user_id=payload.admin_user_id,
        )
    except AdminServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return AdminWalletAdjustmentResponse(
        user_id=payload.user_id,
        operation_id=operation_id,
        amount=payload.amount,
        bucket=payload.bucket,
        total_available=balances.total_available,
        total_reserved=balances.total_reserved,
    )


@router.get("/audit/events", response_model=AdminAuditEventListResponse)
async def admin_list_audit_events(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    target_type: str | None = None,
    action: str | None = None,
) -> AdminAuditEventListResponse:
    """List recent admin audit events."""

    try:
        events = await list_admin_audit_events(
            session,
            limit=limit,
            target_type=target_type,
            action=action,
        )
    except AdminServiceError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return AdminAuditEventListResponse(items=[_admin_audit_event_response(event) for event in events])


async def _wallets_by_user_id(session: AsyncSession, user_ids: list[uuid.UUID]) -> dict[uuid.UUID, Wallet]:
    if not user_ids:
        return {}
    result = await session.execute(select(Wallet).where(Wallet.user_id.in_(user_ids)))
    return {wallet.user_id: wallet for wallet in result.scalars()}


def _admin_user_response(user: object, wallet: Wallet | None) -> AdminUserResponse:
    return AdminUserResponse(
        id=user.id,
        telegram_user_id=user.telegram_user_id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        is_blocked=user.is_blocked,
        can_generate=user.can_generate,
        can_publish_profile=user.can_publish_profile,
        can_publish_feed=user.can_publish_feed,
        can_use_payments=user.can_use_payments,
        cached_available_balance=wallet.cached_available_balance if wallet else None,
        cached_reserved_balance=wallet.cached_reserved_balance if wallet else None,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def _admin_generation_response(task: object) -> AdminGenerationResponse:
    return AdminGenerationResponse(
        id=task.id,
        user_id=task.user_id,
        status=task.status,
        provider=task.provider,
        model_code=task.model_code,
        operation=task.operation,
        reserved_credits=task.reserved_credits,
        charged_credits=task.charged_credits,
        provider_task_id=task.provider_task_id,
        error_code=task.error_code,
        error_message=task.error_message,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def _admin_publication_response(publication: object) -> AdminPublicationResponse:
    return AdminPublicationResponse(
        id=publication.id,
        user_id=publication.user_id,
        asset_id=publication.asset_id,
        visibility=publication.visibility,
        status=publication.status,
        title=publication.title,
        description=publication.description,
        is_explicit=publication.is_explicit,
        blur_required=publication.blur_required,
        published_at=publication.published_at,
        deleted_at=publication.deleted_at,
        media_url=f"/media/assets/{publication.asset_id}/content",
    )


def _admin_payment_order_response(order: object) -> AdminPaymentOrderResponse:
    return AdminPaymentOrderResponse(
        id=order.id,
        user_id=order.user_id,
        provider=order.provider,
        external_payment_id=order.external_payment_id,
        package_code=order.package_code,
        amount_minor=order.amount_minor,
        currency=order.currency,
        credits_amount=order.credits_amount,
        status=order.status,
        expires_at=order.expires_at,
        paid_at=order.paid_at,
        provider_checkout_url=order.provider_checkout_url,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


def _admin_audit_event_response(event: object) -> AdminAuditEventResponse:
    return AdminAuditEventResponse(
        id=event.id,
        admin_user_id=event.admin_user_id,
        target_type=event.target_type,
        target_id=event.target_id,
        action=event.action,
        reason=event.reason,
        before_state=event.before_state,
        after_state=event.after_state,
        created_at=event.created_at,
    )
