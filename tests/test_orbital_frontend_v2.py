from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "apps" / "orbital_web"


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_orbital_frontend_is_fresh_package_with_reference_tokens() -> None:
    assert (WEB / "package.json").exists()
    assert (WEB / "src" / "App.tsx").exists()
    assert (WEB / "src" / "api.ts").exists()
    styles = read("apps/orbital_web/src/styles.css")
    assert "--pink: #ff45a2" in styles
    assert "--cyan: #00f2ff" in styles
    assert "--lime: #a0f11c" in styles
    assert "width: 280px" in styles
    assert "scanline-layer" in styles


def test_orbital_frontend_uses_existing_core_api_contracts() -> None:
    api = read("apps/orbital_web/src/api.ts")
    for endpoint in [
        "/auth/web-session",
        "/adult-consent/accept",
        "/feed?limit=",
        "/workspace/avatars",
        "/generations",
        "/profiles/me",
        "/billing/packages",
        "/wallet/me",
    ]:
        assert endpoint in api
    assert "seedream-5-pro-text-to-image" in api
    assert "seedream-5-pro-image-to-image" in api
    assert "seedance-2.0" in api


def test_orbital_product_brief_documents_fresh_rebuild_and_e2e_plan() -> None:
    brief = read("docs/FRONTEND_PRODUCT_BRIEF_V2.md")
    assert "fresh UI package" in brief
    assert "Product flow map" in brief
    assert "Route wireframes" in brief
    assert "Component system decision" in brief
    assert "E2E test plan" in brief
    assert "must not be called production-ready" in brief
