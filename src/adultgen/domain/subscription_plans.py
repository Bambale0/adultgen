"""Subscription plan catalog for recurring credit grants."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True, slots=True)
class SubscriptionPlan:
    """Static subscription plan metadata exposed by billing APIs."""

    code: str
    title: str
    credits_per_period: int
    amount_minor: int
    currency: str
    period_days: int
    rollover_policy: str
    description: str
    is_popular: bool = False

    @property
    def amount_major(self) -> str:
        """Return human-friendly decimal amount."""

        return f"{self.amount_minor / 100:.2f}"

    @property
    def period_delta(self) -> timedelta:
        """Return plan period as a timedelta."""

        return timedelta(days=self.period_days)


SUBSCRIPTION_PLANS: tuple[SubscriptionPlan, ...] = (
    SubscriptionPlan(
        code="starter_monthly",
        title="Starter Monthly",
        credits_per_period=700,
        amount_minor=99000,
        currency="RUB",
        period_days=30,
        rollover_policy="expires_each_period",
        description="Monthly starter bundle for light website Studio usage.",
    ),
    SubscriptionPlan(
        code="creator_monthly",
        title="Creator Monthly",
        credits_per_period=2500,
        amount_minor=249000,
        currency="RUB",
        period_days=30,
        rollover_policy="expires_each_period",
        description="Popular monthly creator bundle for regular image and video generations.",
        is_popular=True,
    ),
    SubscriptionPlan(
        code="studio_monthly",
        title="Studio Monthly",
        credits_per_period=7500,
        amount_minor=599000,
        currency="RUB",
        period_days=30,
        rollover_policy="expires_each_period",
        description="High-volume monthly plan for production content workflows.",
    ),
)


def list_subscription_plans() -> list[SubscriptionPlan]:
    """Return enabled subscription plans."""

    return list(SUBSCRIPTION_PLANS)


def get_subscription_plan(code: str) -> SubscriptionPlan:
    """Return a subscription plan by code."""

    for plan in SUBSCRIPTION_PLANS:
        if plan.code == code:
            return plan
    raise KeyError(f"Unknown subscription plan: {code}")
