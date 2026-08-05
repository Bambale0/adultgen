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


def test_web_api_exposes_wallet_balance_client() -> None:
    api = read("apps/web_app/src/api.ts")

    assert "type WalletBalance" in api
    assert "type WalletBucketBalance" in api
    assert "fetchWalletBalance" in api
    assert "'/wallet/me'" in api


def test_web_billing_page_shows_wallet_balance() -> None:
    app = read("apps/web_app/src/App.tsx")

    assert "walletBalance" in app
    assert "WalletBalanceCard" in app
    assert "fetchWalletBalance(session.access_token)" in app
    assert "Обновить баланс" in app
    assert "Available" in app
    assert "Reserved" in app
    assert "total_available" in app
    assert "total_reserved" in app


def test_wallet_balance_fetch_uses_effect_cleanup() -> None:
    app = read("apps/web_app/src/App.tsx")

    assert "if (!session || activeRoute.id !== 'billing') return" in app
    assert "let ignore = false" in app
    assert "if (!ignore) setWalletBalance(result)" in app
    assert "ignore = true" in app
