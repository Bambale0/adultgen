from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_wallet_router_is_registered() -> None:
    core_api = read("src/adultgen/apps/core_api.py")
    router = read("src/adultgen/api/routers/wallets.py")
    schema = read("src/adultgen/api/schemas/wallets.py")

    assert "wallets," in core_api
    assert "app.include_router(wallets.router)" in core_api
    assert '@router.get("/me"' in router
    assert "project_wallet_from_db" in router
    assert "WalletBalanceResponse" in schema
    assert "WalletBucketBalanceResponse" in schema


def test_orbital_api_exposes_wallet_balance_client() -> None:
    api = read("apps/orbital_web/src/api.ts")

    assert "export type WalletBalance" in api
    assert "total_available: number" in api
    assert "total_reserved: number" in api
    assert "wallet(token: string)" in api
    assert "'/wallet/me'" in api


def test_orbital_billing_page_shows_wallet_projection() -> None:
    app = read("apps/orbital_web/src/App.tsx")

    assert "function BillingScreen(" in app
    assert "AVAILABLE POWER" in app
    assert "wallet?.total_available" in app
    assert "wallet?.total_reserved" in app
    assert "wallet?.total_balance" in app
    assert "CREDITS" in app


def test_wallet_refresh_uses_existing_core_ledger_projection() -> None:
    app = read("apps/orbital_web/src/App.tsx")

    assert "api.wallet(session.access_token).then(setWallet)" in app
    assert "setWallet(balance)" in app
    assert "FINAL CHARGE BY BACKEND LEDGER" in app
