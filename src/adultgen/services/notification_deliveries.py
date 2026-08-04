"""Notification delivery application service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.db.models.notifications import NotificationDelivery
from adultgen.domain.delivery_retry import decide_delivery_retry
from adultgen.domain.enums import NotificationDeliveryStatus


async def create_notification_delivery(
    session: AsyncSession,
    *,
    telegram_channel_id: uuid.UUID,
    telegram_chat_id: int,
    user_id: uuid.UUID | None = None,
    generation_task_id: uuid.UUID | None = None,
    payload: dict[str, object] | None = None,
) -> NotificationDelivery:
    """Create a pending notification delivery log."""

    delivery = NotificationDelivery(
        user_id=user_id,
        telegram_channel_id=telegram_channel_id,
        generation_task_id=generation_task_id,
        telegram_chat_id=telegram_chat_id,
        delivery_status=NotificationDeliveryStatus.PENDING.value,
        attempts=0,
        payload=payload or {},
    )
    session.add(delivery)
    await session.flush()
    return delivery


async def mark_notification_delivery_success(
    session: AsyncSession,
    *,
    delivery_id: uuid.UUID,
    telegram_message_id: int,
    now: datetime | None = None,
) -> NotificationDelivery:
    """Mark a notification delivery as delivered."""

    delivery = await _get_delivery_for_update(session, delivery_id)
    delivery.delivery_status = NotificationDeliveryStatus.DELIVERED.value
    delivery.telegram_message_id = telegram_message_id
    delivery.delivered_at = now or datetime.now(UTC)
    delivery.last_error = None
    delivery.next_retry_at = None
    await session.flush()
    return delivery


async def mark_notification_delivery_failure(
    session: AsyncSession,
    *,
    delivery_id: uuid.UUID,
    error_message: str,
    now: datetime | None = None,
    max_attempts: int = 3,
) -> NotificationDelivery:
    """Mark failed attempt and either schedule retry or finalize failure."""

    delivery = await _get_delivery_for_update(session, delivery_id)
    resolved_now = now or datetime.now(UTC)
    decision = decide_delivery_retry(
        previous_attempts=delivery.attempts,
        now=resolved_now,
        max_attempts=max_attempts,
    )

    delivery.attempts = decision.attempts
    delivery.last_error = error_message
    delivery.next_retry_at = decision.next_retry_at
    delivery.delivery_status = (
        NotificationDeliveryStatus.RETRY_SCHEDULED.value
        if decision.should_retry
        else NotificationDeliveryStatus.FAILED.value
    )
    await session.flush()
    return delivery


async def list_due_notification_retries(
    session: AsyncSession,
    *,
    now: datetime | None = None,
    limit: int = 100,
) -> list[NotificationDelivery]:
    """List delivery records ready for retry."""

    if limit <= 0:
        raise ValueError("Retry list limit must be positive.")

    resolved_now = now or datetime.now(UTC)
    result = await session.execute(
        select(NotificationDelivery)
        .where(
            NotificationDelivery.delivery_status
            == NotificationDeliveryStatus.RETRY_SCHEDULED.value,
            NotificationDelivery.next_retry_at.is_not(None),
            NotificationDelivery.next_retry_at <= resolved_now,
        )
        .order_by(NotificationDelivery.next_retry_at)
        .limit(limit)
    )
    return list(result.scalars())


async def _get_delivery_for_update(
    session: AsyncSession,
    delivery_id: uuid.UUID,
) -> NotificationDelivery:
    result = await session.execute(
        select(NotificationDelivery).where(NotificationDelivery.id == delivery_id).with_for_update()
    )
    delivery = result.scalar_one_or_none()
    if delivery is None:
        raise ValueError("Notification delivery not found.")
    return delivery
