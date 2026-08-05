from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_use_web_route_hook_syncs_url_and_browser_history() -> None:
    hook = read("apps/web_app/src/hooks/useWebRoute.ts")

    assert "export function useWebRoute" in hook
    assert "findRouteByPath(window.location.pathname)" in hook
    assert "window.addEventListener('popstate'" in hook
    assert "window.removeEventListener('popstate'" in hook
    assert "window.history.pushState" in hook
    assert "route.path" in hook
    assert "routeId: route.id" in hook


def test_frontend_roadmap_tracks_route_shell_as_second_epic() -> None:
    roadmap = read("docs/FRONTEND_AUDIT_ROADMAP.md")

    assert "Epic FE-02 — App shell and routing hardening" in roadmap
    assert "useWebRoute" in roadmap
    assert "URL synchronization with `history.pushState`" in roadmap
    assert "`popstate` support" in roadmap


def test_routes_keep_metadata_needed_by_route_hook() -> None:
    routes = read("apps/web_app/src/routes.ts")

    assert "export type WebAppRouteId" in routes
    assert "path: string" in routes
    assert "findRouteByPath" in routes
    assert "webAppRoutes.find((route) => route.path === pathname)" in routes


def test_routed_user_app_wires_route_hook_to_user_shell() -> None:
    routed_user_app = read("apps/web_app/src/RoutedUserApp.tsx")
    main = read("apps/web_app/src/main.tsx")

    assert "useWebRoute" in routed_user_app
    assert "window.addEventListener('click'" in routed_user_app
    assert "window.addEventListener('change'" in routed_user_app
    assert "routeFromButton" in routed_user_app
    assert "routeFromSelect" in routed_user_app
    assert "<App key={activeRoute.path}" in routed_user_app
    assert "RoutedUserApp" in main
    assert "window.location.pathname.startsWith('/admin')" in main
