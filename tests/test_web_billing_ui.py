from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_orbital_api_exposes_billing_client_methods() -> None:
    api = read("apps/orbital_web/src/api.ts")

    assert "export type CreditPackage" in api
    assert "export type PaymentOrder" in api
    assert "packages()" in api
    assert "createPaymentOrder(token: string, packageCode: string)" in api
    assert "checkout(token: string, orderId: string)" in api
    assert "'/billing/packages'" in api
    assert "'/billing/orders'" in api
    assert "`/billing/orders/${orderId}/crocopay`" in api


def test_billing_route_renders_real_checkout_flow() -> None:
    app = read("apps/orbital_web/src/App.tsx")

    assert "function BillingScreen(" in app
    assert "const [packages, setPackages]" in app
    assert "const [selected, setSelected]" in app
    assert "api.createPaymentOrder(session.access_token, selected)" in app
    assert "api.checkout(session.access_token, order.id)" in app
    assert "window.open(result.redirect_url, '_blank'" in app
    assert "INITIATE PAYMENT CHANNEL" in app


def test_billing_screen_fetches_packages_and_wallet_from_core() -> None:
    app = read("apps/orbital_web/src/App.tsx")

    assert "api.packages().then" in app
    assert "api.wallet(session.access_token).then(setWallet)" in app
    assert "setSelected((value) => value || result.items[0]?.code || '')" in app


def test_billing_styles_are_present() -> None:
    styles = read("apps/orbital_web/src/styles.css")

    assert ".wallet-hero" in styles
    assert ".package-grid" in styles
    assert ".package-card.selected" in styles
    assert ".billing-launch" in styles
