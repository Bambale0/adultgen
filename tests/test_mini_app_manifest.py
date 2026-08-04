import json
from pathlib import Path
MANIFEST_PATH = Path("apps/mini_app/routes.manifest.json")


def test_mini_app_manifest_contains_all_mvp_pages() -> None:
    routes = json.loads(MANIFEST_PATH.read_text())
    route_ids = {route["id"] for route in routes}

    assert route_ids == {
        "home",
        "feed",
        "create",
        "projects",
        "profile",
        "avatars",
        "balance",
        "partner",
        "settings",
        "support",
    }


def test_feed_route_requires_adult_consent() -> None:
    routes = json.loads(MANIFEST_PATH.read_text())
    feed_route = next(route for route in routes if route["id"] == "feed")

    assert feed_route["requiresAdultConsent"] is True


def test_all_mini_app_routes_require_auth() -> None:
    routes = json.loads(MANIFEST_PATH.read_text())

    assert all(route["requiresAuth"] for route in routes)
