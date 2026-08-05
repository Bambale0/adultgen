"""Subscription service for plan activation and recurring credit grants."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.db.models.subscriptions import SubscriptionCreditGrant, UserSubscription
from adultgen.domain.enums import CreditBucket, WalletEntryType
from adultgen.domain.subscription_plans import SubscriptionPlan, get_subscription_plan, list_subscription_plans
from adultgen.services.wallets import credit_wallet

ACTIVE_STATUS = "active"
CANCELLED_STATUS = "cancelled"


class SubscriptionServiceError(ValueError):
    """Raised when a subscription operation is invalid."""


@dataclass(frozen=True, slots=True)
class SubscriptionActivationResult:
    """Activated subscription plus whether credits were granted now."""

    subscription: UserSubscription
    plan: SubscriptionPlan
    granted_now: bool
    grant: SubscriptionCreditGrant | None


async def list_plans() -> list[SubscriptionPlan]:
    """Return enabled subscription plans."""

    return list_subscription_plans()


async def get_active_subscription(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
) -> UserSubscription | None:
    """Return the user's active subscription, if any."""

    result = await session.execute(
        select(UserSubscription)
        .where(UserSubscription.user_id == user_id, UserSubscription.status == ACTIVE_STATUS)
        .order_by(UserSubscription.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def activate_subscription(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    plan_code: str,
    provider: str | None = None,
    provider_subscription_id: str | None = None,
    now: datetime | None = None,
) -> SubscriptionActivationResult:
    """Activate a plan-backed subscription and grant the first period credits."""

    current_time = now or datetime.now(UTC)
    plan = _get_plan(plan_code)
    active = await get_active_subscription(session, user_id=user_id)
    if active and active.plan_code != plan.code:
        raise SubscriptionServiceError("User already has another active subscription.")

    if active:
        subscription = active
    else:
        subscription = UserSubscription(
            user_id=user_id,
            plan_code=plan.code,
            status=ACTIVE_STATUS,
            provider=provider,
            provider_subscription_id=provider_subscription_id,
            current_period_start=current_time,
            current_period_end=current_time + plan.period_delta,
        )
        session.add(subscription)
        await session.flush()

    grant = await grant_current_period_credits(session, subscription=subscription, plan=plan)
    return SubscriptionActivationResult(
        subscription=subscription,
        plan=plan,
        granted_now=grant is not None,
        grant=grant,
    )


async def grant_current_period_credits(
    session: AsyncSession,
    *,
    subscription: UserSubscription,
    plan: SubscriptionPlan | None = None,
) -> SubscriptionCreditGrant | None:
    """Grant subscription credits for the current period exactly once."""

    resolved_plan = plan or _get_plan(subscription.plan_code)
    existing = await _find_existing_grant(session, subscription=subscription)
    if existing:
        return None

    operation_id = uuid.uuid4()
    grant = SubscriptionCreditGrant(
        subscription_id=subscription.id,
        user_id=subscription.user_id,
        plan_code=subscription.plan_code,
        credits_amount=resolved_plan.credits_per_period,
        period_start=subscription.current_period_start,
        period_end=subscription.current_period_end,
        wallet_entry_operation_id=operation_id,
    )
    session.add(grant)
    await session.flush()

    await credit_wallet(
        session,
        user_id=subscription.user_id,
        amount=resolved_plan.credits_per_period,
        bucket=CreditBucket.SUBSCRIPTION,
        entry_type=WalletEntryType.SUBSCRIPTION_CREDIT,
        operation_id=operation_id,
        reason=f"Subscription grant for {subscription.plan_code}",
    )
    subscription.last_granted_at = datetime.now(UTC)
    await session.flush()
    return grant


async def cancel_subscription_at_period_end(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
) -> UserSubscription:
    """Mark the active subscription to cancel at the current period end."""

    subscription = await get_active_subscription(session, user_id=user_id)
    if not subscription:
        raise SubscriptionServiceError("Active subscription not found.")
    subscription.cancel_at_period_end = True
    subscription.cancelled_at = datetime.now(UTC)
    await session.flush()
    return subscription


async def _find_existing_grant(
    session: AsyncSession,
    *,
    subscription: UserSubscription,
) -> SubscriptionCreditGrant | None:
    result = await session.execute(
        select(SubscriptionCreditGrant).where(
            SubscriptionCreditGrant.subscription_id == subscription.id,
            SubscriptionCreditGrant.period_start == subscription.current_period_start,
            SubscriptionCreditGrant.period_end == subscription.current_period_end,
        )
    )
    return result.scalar_one_or_none()


def _get_plan(plan_code: str) -> SubscriptionPlan:
    try:
        return get_subscription_plan(plan_code)
    except KeyError as exc:
        raise SubscriptionServiceError(str(exc)) from exc
