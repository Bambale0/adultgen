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
