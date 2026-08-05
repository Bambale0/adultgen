"""Admin API routes."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
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
    AdminPublicationListResponse,
    AdminPublicationResponse,
    AdminPublicationStatusRequest,
    AdminUserFlagsPatchRequest,
    AdminUserListResponse,
    AdminUserResponse,
    AdminWalletAdjustmentRequest,
    AdminWalletAdjustmentResponse,
)
from adultgen.db.models.audit import AdminAuditEvent
from adultgen.db.models.generations import GenerationTask
from adultgen.db.models.payments import PaymentOrder
from adultgen.db.models.publications import Publication
from adultgen.db.models.users import User
from adultgen.domain.enums import CreditBucket, PublicationStatus, WalletEntryType
from adultgen.services.admin_audit import record_admin_audit_event
from adultgen.services.wallets import credit_wallet

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
async def list_admin_users(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    blocked: bool | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> AdminUserListResponse:
    """List users for admin review."""

    query = select(User).order_by(User.created_at.desc()).limit(limit)
    if blocked is not None:
        query = query.where(User.is_blocked == blocked)
    result = await session.execute(query)
    return AdminUserListResponse(items=[_user_response(user) for user in result.scalars()])


@router.get("/users/{user_id}", response_model=AdminUserResponse)
async def get_admin_user(
    user_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AdminUserResponse:
    """Return one user for admin review."""

    user = await _get_user_or_404(session, user_id)
    return _user_response(user)


@router.patch("/users/{user_id}/flags", response_model=AdminUserResponse)
async def patch_admin_user_flags(
    user_id: uuid.UUID,
    payload: AdminUserFlagsPatchRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AdminUserResponse:
    """Patch user moderation/capability flags."""

    user = await _get_user_or_404(session, user_id)
    before = _user_flag_state(user)
    patch = payload.model_dump(exclude={"reason", "admin_user_id"}, exclude_none=True)
    if not patch:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No flags supplied.")

    for field, value in patch.items():
        setattr(user, field, value)
    await session.flush()
    after = _user_flag_state(user)
    await record_admin_audit_event(
        session,
        admin_user_id=payload.admin_user_id,
        target_type="user",
        target_id=user.id,
        action="patch_user_flags",
        reason=payload.reason,
        before_state=before,
        after_state=after,
    )
    return _user_response(user)


@router.get("/generations", response_model=AdminGenerationListResponse)
async def list_admin_generations(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    user_id: uuid.UUID | None = None,
    task_status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> AdminGenerationListResponse:
    """List generation tasks for support/debugging."""

    query = select(GenerationTask).order_by(GenerationTask.created_at.desc()).limit(limit)
    if user_id is not None:
        query = query.where(GenerationTask.user_id == user_id)
    if task_status is not None:
        query = query.where(GenerationTask.status == task_status)
    result = await session.execute(query)
    return AdminGenerationListResponse(items=[_generation_response(task) for task in result.scalars()])


@router.get("/publications", response_model=AdminPublicationListResponse)
async def list_admin_publications(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    publication_status: str | None = None,
    visibility: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> AdminPublicationListResponse:
    """List publications for moderation/support."""

    query = select(Publication).order_by(Publication.published_at.desc()).limit(limit)
    if publication_status is not None:
        query = query.where(Publication.status == publication_status)
    if visibility is not None:
        query = query.where(Publication.visibility == visibility)
    result = await session.execute(query)
    return AdminPublicationListResponse(items=[_publication_response(item) for item in result.scalars()])


@router.patch("/publications/{publication_id}/status", response_model=AdminPublicationResponse)
async def patch_admin_publication_status(
    publication_id: uuid.UUID,
    payload: AdminPublicationStatusRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AdminPublicationResponse:
    """Change publication moderation status."""

    publication = await _get_publication_or_404(session, publication_id)
    allowed_statuses = {status_item.value for status_item in PublicationStatus}
    if payload.status not in allowed_statuses:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid publication status.")

    before = _publication_state(publication)
    publication.status = payload.status
    publication.deleted_at = datetime.now(UTC) if payload.status == PublicationStatus.DELETED.value else None
    await session.flush()
    after = _publication_state(publication)
    await record_admin_audit_event(
        session,
        admin_user_id=payload.admin_user_id,
        target_type="publication",
        target_id=publication.id,
        action="patch_publication_status",
        reason=payload.reason,
        before_state=before,
        after_state=after,
    )
    return _publication_response(publication)


@router.get("/payments/orders", response_model=AdminPaymentOrderListResponse)
async def list_admin_payment_orders(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    order_status: str | None = None,
    user_id: uuid.UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> AdminPaymentOrderListResponse:
    """List payment orders for finance support."""

    query = select(PaymentOrder).order_by(PaymentOrder.created_at.desc()).limit(limit)
    if order_status is not None:
        query = query.where(PaymentOrder.status == order_status)
    if user_id is not None:
        query = query.where(PaymentOrder.user_id == user_id)
    result = await session.execute(query)
    return AdminPaymentOrderListResponse(items=[_payment_order_response(order) for order in result.scalars()])


@router.post("/wallet-adjustments", response_model=AdminWalletAdjustmentResponse)
async def create_admin_wallet_adjustment(
    payload: AdminWalletAdjustmentRequest,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AdminWalletAdjustmentResponse:
    """Create a manual wallet adjustment through the immutable wallet ledger."""

    await _get_user_or_404(session, payload.user_id)
    if payload.amount == 0:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Amount must not be zero.")
    try:
        bucket = CreditBucket(payload.bucket)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid credit bucket.") from exc

    operation_id = uuid.uuid4()
    balances = await credit_wallet(
        session,
        user_id=payload.user_id,
        amount=payload.amount,
        bucket=bucket,
        entry_type=WalletEntryType.ADMIN_ADJUSTMENT,
        operation_id=operation_id,
        admin_user_id=payload.admin_user_id,
        reason=payload.reason,
    )
    await record_admin_audit_event(
        session,
        admin_user_id=payload.admin_user_id,
        target_type="wallet",
        target_id=payload.user_id,
        action="wallet_adjustment",
        reason=payload.reason,
        before_state={},
        after_state={"amount": payload.amount, "bucket": bucket.value, "operation_id": str(operation_id)},
    )
    return AdminWalletAdjustmentResponse(
        user_id=payload.user_id,
        amount=payload.amount,
        bucket=bucket.value,
        total_available=balances.total_available,
        total_reserved=balances.total_reserved,
    )


@router.get("/audit-events", response_model=AdminAuditEventListResponse)
async def list_admin_audit_events(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    target_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> AdminAuditEventListResponse:
    """List recent admin audit events."""

    query = select(AdminAuditEvent).order_by(AdminAuditEvent.created_at.desc()).limit(limit)
    if target_type is not None:
        query = query.where(AdminAuditEvent.target_type == target_type)
    result = await session.execute(query)
    return AdminAuditEventListResponse(items=[_audit_event_response(event) for event in result.scalars()])


async def _get_user_or_404(session: AsyncSession, user_id: uuid.UUID) -> User:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user


async def _get_publication_or_404(session: AsyncSession, publication_id: uuid.UUID) -> Publication:
    result = await session.execute(select(Publication).where(Publication.id == publication_id))
    publication = result.scalar_one_or_none()
    if publication is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Publication not found.")
    return publication


def _user_response(user: User) -> AdminUserResponse:
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
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


def _user_flag_state(user: User) -> dict[str, object]:
    return {
        "is_blocked": user.is_blocked,
        "can_generate": user.can_generate,
        "can_publish_profile": user.can_publish_profile,
        "can_publish_feed": user.can_publish_feed,
        "can_use_payments": user.can_use_payments,
    }


def _generation_response(task: GenerationTask) -> AdminGenerationResponse:
    return AdminGenerationResponse(
        id=task.id,
        user_id=task.user_id,
        provider=task.provider,
        model_code=task.model_code,
        operation=task.operation,
        status=task.status,
        provider_task_id=task.provider_task_id,
        reserved_credits=task.reserved_credits,
        charged_credits=task.charged_credits,
        error_code=task.error_code,
        error_message=task.error_message,
        created_at=task.created_at,
        submitted_at=task.submitted_at,
        completed_at=task.completed_at,
    )


def _publication_response(publication: Publication) -> AdminPublicationResponse:
    return AdminPublicationResponse(
        id=publication.id,
        user_id=publication.user_id,
        asset_id=publication.asset_id,
        title=publication.title,
        visibility=publication.visibility,
        is_explicit=publication.is_explicit,
        blur_required=publication.blur_required,
        status=publication.status,
        published_at=publication.published_at,
        deleted_at=publication.deleted_at,
    )


def _publication_state(publication: Publication) -> dict[str, object]:
    return {
        "status": publication.status,
        "deleted_at": publication.deleted_at.isoformat() if publication.deleted_at else None,
    }


def _payment_order_response(order: PaymentOrder) -> AdminPaymentOrderResponse:
    return AdminPaymentOrderResponse(
        id=order.id,
        user_id=order.user_id,
        provider=order.provider,
        package_code=order.package_code,
        amount_minor=order.amount_minor,
        currency=order.currency,
        credits_amount=order.credits_amount,
        status=order.status,
        external_payment_id=order.external_payment_id,
        provider_checkout_url=order.provider_checkout_url,
        expires_at=order.expires_at,
        paid_at=order.paid_at,
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


def _audit_event_response(event: AdminAuditEvent) -> AdminAuditEventResponse:
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
