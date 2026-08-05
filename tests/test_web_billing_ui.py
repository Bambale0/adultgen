from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_web_api_exposes_billing_client_methods() -> None:
    api = read("apps/web_app/src/api.ts")
    assert "type CreditPackage" in api
    assert "type PaymentOrder" in api
    assert "fetchCreditPackages" in api
    assert "createPaymentOrder" in api
    assert "initiateCrocoPayCheckout" in api
    assert "'/billing/packages'" in api
    assert "'/billing/orders'" in api
    assert "`/billing/orders/${orderId}/crocopay`" in api


def test_billing_route_renders_real_checkout_flow() -> None:
    app = read("apps/web_app/src/App.tsx")
    assert "activeRoute.id === 'billing'" in app
    assert "BillingCard" in app
    assert "creditPackages" in app
    assert "selectedPackageCode" in app
    assert "latestPaymentOrder" in app
    assert "latestCheckout" in app
    assert "handleCreatePaymentOrder" in app
    assert "handleStartCrocoPayCheckout" in app
    assert "window.open(result.redirect_url" in app


def test_billing_ui_uses_stale_response_cleanup_for_packages() -> None:
    app = read("apps/web_app/src/App.tsx")
    assert "if (activeRoute.id !== 'billing') return" in app
    assert "let ignore = false" in app
    assert "if (!ignore)" in app
    assert "ignore = true" in app


def test_billing_styles_are_present() -> None:
    styles = read("apps/web_app/src/styles.css")
    assert ".billing-grid" in styles
    assert ".package-grid" in styles
    assert ".package-card.selected" in styles
    assert ".payment-order-card" in styles
    assert ".checkout-link" in styles
