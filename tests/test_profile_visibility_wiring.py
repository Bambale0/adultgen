from pathlib import Path

CORE_API = Path("src/adultgen/apps/core_api.py")
PROFILE_ROUTER = Path("src/adultgen/api/routers/profiles.py")
PROFILE_SERVICE = Path("src/adultgen/services/profiles.py")
PROFILE_CLIENT = Path("apps/mini_app/src/profile.ts")
PROFILE_PAGE = Path("apps/mini_app/src/profilePage.tsx")
APP_TSX = Path("apps/mini_app/src/App.tsx")


def test_core_api_registers_profile_router() -> None:
    content = CORE_API.read_text()

    assert "profiles" in content
    assert "profiles.router" in content


def test_profile_router_exposes_private_and_public_profile_endpoints() -> None:
    content = PROFILE_ROUTER.read_text()

    assert "/me" in content
    assert "@router.get(\"/{public_id}\"" in content
    assert "get_current_token_claims" in content


def test_profile_service_supports_public_private_visibility() -> None:
    content = PROFILE_SERVICE.read_text()

    assert "PROFILE_PRIVATE" in content
    assert "PROFILE_PUBLIC" in content
    assert "get_public_profile_by_public_id" in content


def test_mini_app_profile_client_calls_backend_profile_endpoints() -> None:
    content = PROFILE_CLIENT.read_text()

    assert "/profiles/me" in content
    assert "PATCH" in content
    assert "Authorization" in content


def test_mini_app_profile_page_toggles_visibility() -> None:
    content = PROFILE_PAGE.read_text()

    assert "fetchMyProfile" in content
    assert "updateMyProfile" in content
    assert "public" in content
    assert "private" in content


def test_app_wires_profile_route_to_profile_page() -> None:
    content = APP_TSX.read_text()

    assert "ProfileVisibilityPage" in content
    assert "activeRoute.id === 'profile'" in content
