from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_orbital_web_has_no_public_admin_route() -> None:
    app = read("apps/orbital_web/src/App.tsx")

    assert "type RouteId = 'feed' | 'studio' | 'missions' | 'profile' | 'billing'" in app
    assert "path: '/admin'" not in app
    assert "ADMIN_API_TOKEN" not in app


def test_orbital_api_client_does_not_embed_admin_credentials() -> None:
    client = read("apps/orbital_web/src/api.ts")

    assert "ADMIN_API_TOKEN" not in client
    assert "adultgen_admin_token" not in client
    assert "fetchAdminUsers" not in client
    assert "createAdminWalletAdjustment" not in client


def test_backend_admin_surface_stays_token_protected() -> None:
    router = read("src/adultgen/api/routers/admin.py")

    assert "require_admin_api_token" in router
    assert '"/users"' in router
    assert '"/generations"' in router
    assert '"/publications"' in router
    assert '"/wallet/adjustments"' in router
    assert '"/audit/events"' in router


def test_product_brief_keeps_admin_as_separate_surface() -> None:
    brief = read("docs/FRONTEND_PRODUCT_BRIEF_V2.md")

    assert "`/admin` — separate future surface" in brief
    assert "Admin remains an independent privileged surface" in brief
    assert "intentionally not mixed into the public/user bundle" in brief


def test_runbook_documents_api_only_admin_foundation() -> None:
    runbook = read("docs/PRODUCTION_DEPLOYMENT.md")

    assert "Admin remains API-only in this foundation PR" in runbook
    assert "/api/admin/*" in runbook
    assert "privileged Orbital admin surface should be delivered separately" in runbook
