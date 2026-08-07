from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_removed_frontend_sources_are_not_restored() -> None:
    legacy = ROOT / "apps" / "web_app"

    assert not (legacy / "package.json").exists()
    assert not (legacy / "src" / "App.tsx").exists()
    assert (ROOT / "apps" / "studio_app").is_dir()


def test_studio_routes_and_generation_contract_are_present() -> None:
    core = read("apps/studio_app/src/core.js")

    for route in ("feed", "create", "projects", "profile", "billing"):
        assert f'"{route}"' in core
    assert "seedream-5-pro-text-to-image" in core
    assert "seedream-5-pro-image-to-image" in core
    assert "seedance-2.0" in core
    assert "escapeHtml" in core


def test_studio_api_client_targets_core_endpoints() -> None:
    api = read("apps/studio_app/src/api.js")

    for endpoint in (
        "/auth/telegram-mini-app",
        "/auth/web-session",
        "/adult-consent",
        "/adult-consent/accept",
        "/feed?limit=",
        "/profiles/",
        "/generations",
    ):
        assert endpoint in api
    assert "Authorization" in api


def test_studio_entry_has_runtime_config_and_adult_gate() -> None:
    index = read("apps/studio_app/public/index.html")
    app = read("apps/studio_app/src/app.js")

    assert "/runtime-config.js" in index
    assert "telegram.org/js/telegram-web-app.js" in index
    assert "ДОСТУП ТОЛЬКО ДЛЯ ВЗРОСЛЫХ" in app
    assert "api.adultConsentStatus()" in app
    assert "api.acceptAdultConsent()" in app
    assert "Core API unavailable; demo mode stays active" in app
