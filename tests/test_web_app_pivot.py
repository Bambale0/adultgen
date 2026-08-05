from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB_APP_ROOT = ROOT / "apps" / "web_app"
ROUTES_FILE = WEB_APP_ROOT / "src" / "routes.ts"
PIVOT_DOC = ROOT / "docs" / "WEB_APP_PIVOT.md"


def test_web_app_pivot_document_exists() -> None:
    content = PIVOT_DOC.read_text(encoding="utf-8")

    assert "Website App -> Core API" in content
    assert "Telegram becomes" in content
    assert "Phase 3B" in content


def test_web_app_foundation_exists() -> None:
    assert (WEB_APP_ROOT / "package.json").exists()
    assert (WEB_APP_ROOT / "index.html").exists()
    assert (WEB_APP_ROOT / "src" / "App.tsx").exists()
    assert ROUTES_FILE.exists()


def test_web_app_route_manifest_has_product_routes_and_guards() -> None:
    content = ROUTES_FILE.read_text(encoding="utf-8")

    for route_id in ["studio", "projects", "avatars", "feed", "collection", "profile", "billing"]:
        assert f"id: '{route_id}'" in content

    assert "requiresAuth: true" in content
    assert "requiresAdultConsent: true" in content
    assert "path: '/studio'" in content
    assert "path: '/feed'" in content
    assert "path: '/billing'" in content
