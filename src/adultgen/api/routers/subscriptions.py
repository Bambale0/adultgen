"""Subscription API routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.api.dependencies import get_current_token_claims, get_db_session
from adultgen.api.schemas.subscriptions import (
    ActivateSubscriptionRequest,
    SubscriptionActivationResponse,
    SubscriptionPlanListResponse,
    SubscriptionPlanResponse,
    SubscriptionResponse,
)
from adultgen.domain.subscription_plans import SubscriptionPlan
from adultgen.services.subscriptions import (
    SubscriptionServiceError,
    activate_subscription,
    cancel_subscription_at_period_end,
    get_active_subscription,
    list_plans,
)
from adultgen.services.tokens import TokenClaims

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("/plans", response_model=SubscriptionPlanListResponse)
async def list_subscription_plan_catalog() -> SubscriptionPlanListResponse:
    """Return enabled subscription plans."""

    return SubscriptionPlanListResponse(items=[_plan_response(plan) for plan in await list_plans()])


@router.get("/me", response_model=SubscriptionResponse | None)
async def get_my_subscription(
    claims: Annotated[TokenClaims, Depends(get_current_token_claims)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SubscriptionResponse | None:
    """Return the current user's active subscription, if present."""

    subscription = await get_active_subscription(session, user_id=claims.user_id)
    return _subscription_response(subscription) if subscription else None


@router.post("/activate", response_model=SubscriptionActivationResponse)
async def activate_my_subscription(
    payload: ActivateSubscriptionRequest,
    claims: Annotated[TokenClaims, Depends(get_current_token_claims)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SubscriptionActivationResponse:
    """Activate an MVP subscription and grant current period credits."""

    try:
        result = await activate_subscription(
            session,
            user_id=claims.user_id,
            plan_code=payload.plan_code,
            provider=payload.provider,
            provider_subscription_id=payload.provider_subscription_id,
        )
    except SubscriptionServiceError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    return SubscriptionActivationResponse(
        subscription=_subscription_response(result.subscription),
        plan=_plan_response(result.plan),
        granted_now=result.granted_now,
        grant_id=result.grant.id if result.grant else None,
        credits_granted=result.grant.credits_amount if result.grant else 0,
    )


@router.post("/me/cancel-at-period-end", response_model=SubscriptionResponse)
async def cancel_my_subscription_at_period_end(
    claims: Annotated[TokenClaims, Depends(get_current_token_claims)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SubscriptionResponse:
    """Mark the current subscription to cancel at period end."""

    try:
        subscription = await cancel_subscription_at_period_end(session, user_id=claims.user_id)
    except SubscriptionServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return _subscription_response(subscription)


def _plan_response(plan: SubscriptionPlan) -> SubscriptionPlanResponse:
    return SubscriptionPlanResponse(
        code=plan.code,
        title=plan.title,
        credits_per_period=plan.credits_per_period,
        amount_minor=plan.amount_minor,
        amount_major=plan.amount_major,
        currency=plan.currency,
        period_days=plan.period_days,
        rollover_policy=plan.rollover_policy,
        description=plan.description,
        is_popular=plan.is_popular,
    )


def _subscription_response(subscription: object) -> SubscriptionResponse:
    return SubscriptionResponse(
        id=subscription.id,
        plan_code=subscription.plan_code,
        status=subscription.status,
        provider=subscription.provider,
        provider_subscription_id=subscription.provider_subscription_id,
        current_period_start=subscription.current_period_start,
        current_period_end=subscription.current_period_end,
        cancel_at_period_end=subscription.cancel_at_period_end,
        cancelled_at=subscription.cancelled_at,
        last_granted_at=subscription.last_granted_at,
    )
