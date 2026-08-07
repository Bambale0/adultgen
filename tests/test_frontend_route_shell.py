from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_orbital_route_shell_syncs_url_and_browser_history() -> None:
    app = read("apps/orbital_web/src/App.tsx")

    assert "function routeFromPath()" in app
    assert "window.location.pathname" in app
    assert "window.addEventListener('popstate'" in app
    assert "window.removeEventListener('popstate'" in app
    assert "window.history.pushState" in app
    assert "setRoute(routeFromPath())" in app


def test_orbital_routes_cover_product_surfaces() -> None:
    app = read("apps/orbital_web/src/App.tsx")

    assert "type RouteId = 'feed' | 'studio' | 'missions' | 'profile' | 'billing'" in app
    for path in ["'/'", "'/studio'", "'/missions'", "'/profile'", "'/billing'"]:
        assert f"path: {path}" in app
    assert "path: '/admin'" not in app


def test_protected_navigation_opens_session_or_age_gate() -> None:
    app = read("apps/orbital_web/src/App.tsx")

    assert "if (next.protected && !session)" in app
    assert "setAuthOpen(true)" in app
    assert "if (next.protected && !consent?.accepted && id !== 'billing')" in app
    assert "setAgeOpen(true)" in app


def test_protected_deep_links_are_guarded_before_react_bootstrap() -> None:
    main = read("apps/orbital_web/src/main.tsx")

    assert "requiresSession" in main
    assert "requiresAdultConsent" in main
    assert "window.history.replaceState({ route: 'feed' }, '', '/')" in main
    assert "['/studio', '/missions', '/profile', '/billing']" in main
