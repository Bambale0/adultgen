from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB_APP_ROOT = ROOT / "apps" / "web_app"
ROUTES_FILE = WEB_APP_ROOT / "src" / "routes.ts"
APP_FILE = WEB_APP_ROOT / "src" / "App.tsx"
API_FILE = WEB_APP_ROOT / "src" / "api.ts"
SESSION_FILE = WEB_APP_ROOT / "src" / "session.ts"
PIVOT_DOC = ROOT / "docs" / "WEB_APP_PIVOT.md"
AUTH_ROUTER = ROOT / "src" / "adultgen" / "api" / "routers" / "auth.py"


def test_web_app_pivot_document_exists() -> None:
    content = PIVOT_DOC.read_text(encoding="utf-8")

    assert "Website App -> Core API" in content
    assert "Telegram becomes" in content
    assert "Phase 3B" in content


def test_web_app_foundation_exists() -> None:
    assert (WEB_APP_ROOT / "package.json").exists()
    assert (WEB_APP_ROOT / "index.html").exists()
    assert APP_FILE.exists()
    assert API_FILE.exists()
    assert SESSION_FILE.exists()
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


def test_web_app_mvp_wires_studio_core_api_and_safety_gate() -> None:
    app_content = APP_FILE.read_text(encoding="utf-8")
    api_content = API_FILE.read_text(encoding="utf-8")

    assert "Generation Studio" in app_content
    assert "Negative prompt" in app_content
    assert "reference_urls" in app_content
    assert "createGenerationTask" in app_content
    assert "acceptAdultConsent" in app_content
    assert "createStarterWorkspace" in app_content
    assert "non-consensual identity" in app_content
    assert "/generations" in api_content
    assert "/workspace/avatars" in api_content
    assert "/adult-consent/accept" in api_content


def test_web_auth_endpoint_exists_for_standalone_site() -> None:
    content = AUTH_ROUTER.read_text(encoding="utf-8")

    assert '@router.post("/web-session"' in content
    assert "upsert_user_from_web_session" in content
    assert "WebSessionAuthResponse" in content
