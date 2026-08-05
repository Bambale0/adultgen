"""Admin service operations and audit helpers."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.db.models.audit import AdminAuditEvent
from adultgen.db.models.generations import GenerationTask
from adultgen.db.models.payments import PaymentOrder
from adultgen.db.models.publications import Publication
from adultgen.db.models.users import User
from adultgen.domain.enums import CreditBucket, PublicationStatus, WalletEntryType
from adultgen.domain.wallet_ledger import WalletBalances
from adultgen.services.wallets import credit_wallet


class AdminServiceError(ValueError):
    """Raised when an admin action cannot be completed."""


async def list_admin_users(
    session: AsyncSession,
    *,
    limit: int = 50,
    blocked: bool | None = None,
) -> list[User]:
    """List users for the admin table."""

    _validate_limit(limit)
    statement = select(User).order_by(User.created_at.desc()).limit(limit)
    if blocked is not None:
        statement = statement.where(User.is_blocked == blocked)
    result = await session.execute(statement)
    return list(result.scalars())


async def update_user_capabilities(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    reason: str,
    admin_user_id: uuid.UUID | None = None,
    **updates: bool | None,
) -> User:
    """Update moderation/payment capabilities for a user and audit the change."""

    user = await _get_user(session, user_id)
    allowed_fields = {
        "is_blocked",
        "can_generate",
        "can_publish_profile",
        "can_publish_feed",
        "can_use_payments",
    }
    clean_updates = {
        field: value for field, value in updates.items() if field in allowed_fields and value is not None
    }
    if not clean_updates:
        raise AdminServiceError("No capability fields supplied.")

    before = _user_capabilities_state(user)
    for field, value in clean_updates.items():
        setattr(user, field, value)
    await session.flush()
    await record_admin_audit_event(
        session,
        admin_user_id=admin_user_id,
        target_type="user",
        target_id=user.id,
        action="update_user_capabilities",
        reason=reason,
        before_state=before,
        after_state=_user_capabilities_state(user),
    )
    return user


async def list_admin_generations(
    session: AsyncSession,
    *,
    limit: int = 50,
    status: str | None = None,
    user_id: uuid.UUID | None = None,
) -> list[GenerationTask]:
    """List generation tasks for admin inspection."""

    _validate_limit(limit)
    statement = select(GenerationTask).order_by(GenerationTask.created_at.desc()).limit(limit)
    if status:
        statement = statement.where(GenerationTask.status == status)
    if user_id:
        statement = statement.where(GenerationTask.user_id == user_id)
    result = await session.execute(statement)
    return list(result.scalars())


async def list_admin_publications(
    session: AsyncSession,
    *,
    limit: int = 50,
    status: str | None = None,
    visibility: str | None = None,
    user_id: uuid.UUID | None = None,
) -> list[Publication]:
    """List publications for admin inspection."""

    _validate_limit(limit)
    statement = select(Publication).order_by(Publication.published_at.desc()).limit(limit)
    if status:
        statement = statement.where(Publication.status == status)
    if visibility:
        statement = statement.where(Publication.visibility == visibility)
    if user_id:
        statement = statement.where(Publication.user_id == user_id)
    result = await session.execute(statement)
    return list(result.scalars())


async def apply_publication_admin_action(
    session: AsyncSession,
    *,
    publication_id: uuid.UUID,
    action: str,
    reason: str,
    admin_user_id: uuid.UUID | None = None,
) -> Publication:
    """Hide, restore, or soft-delete a publication through the admin API."""

    publication = await _get_publication(session, publication_id)
    normalized_action = action.casefold().strip()
    if normalized_action not in {"hide", "restore", "delete"}:
        raise AdminServiceError("Unknown publication action.")

    before = _publication_state(publication)
    if normalized_action == "hide":
        publication.status = PublicationStatus.HIDDEN.value
    elif normalized_action == "restore":
        publication.status = PublicationStatus.ACTIVE.value
        publication.deleted_at = None
    else:
        publication.status = PublicationStatus.DELETED.value
        publication.deleted_at = datetime.now(UTC)

    await session.flush()
    await record_admin_audit_event(
        session,
        admin_user_id=admin_user_id,
        target_type="publication",
        target_id=publication.id,
        action=f"publication_{normalized_action}",
        reason=reason,
        before_state=before,
        after_state=_publication_state(publication),
    )
    return publication


async def list_admin_payment_orders(
    session: AsyncSession,
    *,
    limit: int = 50,
    status: str | None = None,
    provider: str | None = None,
    user_id: uuid.UUID | None = None,
) -> list[PaymentOrder]:
    """List payment orders for admin inspection."""

    _validate_limit(limit)
    statement = select(PaymentOrder).order_by(PaymentOrder.created_at.desc()).limit(limit)
    if status:
        statement = statement.where(PaymentOrder.status == status)
    if provider:
        statement = statement.where(PaymentOrder.provider == provider)
    if user_id:
        statement = statement.where(PaymentOrder.user_id == user_id)
    result = await session.execute(statement)
    return list(result.scalars())


async def adjust_user_wallet(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    amount: int,
    bucket: CreditBucket,
    reason: str,
    admin_user_id: uuid.UUID | None = None,
) -> tuple[uuid.UUID, WalletBalances]:
    """Credit a user wallet through the append-only ledger and audit the action."""

    await _get_user(session, user_id)
    operation_id = uuid.uuid4()
    balances = await credit_wallet(
        session,
        user_id=user_id,
        amount=amount,
        bucket=bucket,
        entry_type=WalletEntryType.ADMIN_ADJUSTMENT,
        operation_id=operation_id,
        reason=reason,
    )
    await record_admin_audit_event(
        session,
        admin_user_id=admin_user_id,
        target_type="wallet",
        target_id=user_id,
        action="wallet_adjustment_credit",
        reason=reason,
        before_state={},
        after_state={
            "operation_id": str(operation_id),
            "amount": amount,
            "bucket": bucket.value,
            "total_available": balances.total_available,
            "total_reserved": balances.total_reserved,
        },
    )
    return operation_id, balances


async def list_admin_audit_events(
    session: AsyncSession,
    *,
    limit: int = 50,
    target_type: str | None = None,
    action: str | None = None,
) -> list[AdminAuditEvent]:
    """List recent admin audit events."""

    _validate_limit(limit)
    statement = select(AdminAuditEvent).order_by(AdminAuditEvent.created_at.desc()).limit(limit)
    if target_type:
        statement = statement.where(AdminAuditEvent.target_type == target_type)
    if action:
        statement = statement.where(AdminAuditEvent.action == action)
    result = await session.execute(statement)
    return list(result.scalars())


async def record_admin_audit_event(
    session: AsyncSession,
    *,
    admin_user_id: uuid.UUID | None,
    target_type: str,
    target_id: uuid.UUID | None,
    action: str,
    reason: str | None,
    before_state: dict[str, Any],
    after_state: dict[str, Any],
) -> AdminAuditEvent:
    """Append an admin audit event."""

    event = AdminAuditEvent(
        admin_user_id=admin_user_id,
        target_type=target_type,
        target_id=target_id,
        action=action,
        reason=reason,
        before_state=before_state,
        after_state=after_state,
    )
    session.add(event)
    await session.flush()
    return event


def _validate_limit(limit: int) -> None:
    if limit <= 0 or limit > 100:
        raise AdminServiceError("Limit must be between 1 and 100.")


async def _get_user(session: AsyncSession, user_id: uuid.UUID) -> User:
    result = await session.execute(select(User).where(User.id == user_id).with_for_update())
    user = result.scalar_one_or_none()
    if user is None:
        raise AdminServiceError("User not found.")
    return user


async def _get_publication(session: AsyncSession, publication_id: uuid.UUID) -> Publication:
    result = await session.execute(
        select(Publication).where(Publication.id == publication_id).with_for_update()
    )
    publication = result.scalar_one_or_none()
    if publication is None:
        raise AdminServiceError("Publication not found.")
    return publication


def _user_capabilities_state(user: User) -> dict[str, Any]:
    return {
        "is_blocked": user.is_blocked,
        "can_generate": user.can_generate,
        "can_publish_profile": user.can_publish_profile,
        "can_publish_feed": user.can_publish_feed,
        "can_use_payments": user.can_use_payments,
    }


def _publication_state(publication: Publication) -> dict[str, Any]:
    return {
        "status": publication.status,
        "visibility": publication.visibility,
        "deleted_at": publication.deleted_at.isoformat() if publication.deleted_at else None,
    }
