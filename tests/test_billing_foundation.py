from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_billing_router_is_registered() -> None:
    core_api = read("src/adultgen/apps/core_api.py")
    assert "billing," in core_api
    assert "app.include_router(billing.router)" in core_api


def test_credit_packages_are_available() -> None:
    catalog = read("src/adultgen/domain/credit_packages.py")
    assert "starter_500" in catalog
    assert "creator_1500" in catalog
    assert "studio_5000" in catalog
    assert "get_credit_package" in catalog


def test_crocopay_signature_contract_is_implemented() -> None:
    integration = read("src/adultgen/integrations/payments/crocopay.py")
    for field in ("timestamp", "subtotal", "percentage", "charge_percentage", "charge_fixed", "total"):
        assert field in integration
    assert "hmac.new" in integration
    assert "compare_digest" in integration
    assert "/api/v2/initiate-payment" in integration


def test_billing_routes_cover_packages_orders_and_provider_checkout() -> None:
    router = read("src/adultgen/api/routers/billing.py")
    assert '@router.get("/packages"' in router
    assert '@router.post("/orders"' in router
    assert '@router.post("/orders/{order_id}/crocopay"' in router
    assert "initiate_crocopay_payment" in router


def test_crocopay_webhook_credits_wallet_once() -> None:
    webhooks = read("src/adultgen/api/routers/webhooks.py")
    billing_service = read("src/adultgen/services/billing.py")
    assert '@router.post("/payments/crocopay"' in webhooks
    assert "verify_crocopay_callback" in webhooks
    assert "PaymentWebhookRaw" in webhooks
    assert "PaymentWebhookProcessing" in webhooks
    assert "WalletEntryType.PAYMENT_CREDIT" in billing_service
    assert "CreditBucket.PURCHASED" in billing_service
    assert "current_status == PaymentOrderStatus.PAID" in billing_service
