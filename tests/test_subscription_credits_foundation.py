from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_subscription_plan_catalog_exists() -> None:
    catalog = read("src/adultgen/domain/subscription_plans.py")

    assert "starter_monthly" in catalog
    assert "creator_monthly" in catalog
    assert "studio_monthly" in catalog
    assert "credits_per_period" in catalog
    assert "rollover_policy" in catalog
    assert "expires_each_period" in catalog


def test_subscription_models_are_registered() -> None:
    models = read("src/adultgen/db/models/subscriptions.py")
    registry = read("src/adultgen/db/models/__init__.py")

    assert "class UserSubscription" in models
    assert "class SubscriptionCreditGrant" in models
    assert 'UniqueConstraint("subscription_id", "period_start", "period_end")' in models
    assert "UserSubscription" in registry
    assert "SubscriptionCreditGrant" in registry


def test_subscription_service_grants_subscription_bucket_once() -> None:
    service = read("src/adultgen/services/subscriptions.py")

    assert "grant_current_period_credits" in service
    assert "SubscriptionCreditGrant" in service
    assert "CreditBucket.SUBSCRIPTION" in service
    assert "WalletEntryType.SUBSCRIPTION_CREDIT" in service
    assert "_find_existing_grant" in service
    assert "return None" in service


def test_subscription_router_is_registered_and_exposes_lifecycle() -> None:
    core_api = read("src/adultgen/apps/core_api.py")
    router = read("src/adultgen/api/routers/subscriptions.py")

    assert "subscriptions," in core_api
    assert "app.include_router(subscriptions.router)" in core_api
    assert '@router.get("/plans"' in router
    assert '@router.get("/me"' in router
    assert '@router.post("/activate"' in router
    assert '@router.post("/me/cancel-at-period-end"' in router
