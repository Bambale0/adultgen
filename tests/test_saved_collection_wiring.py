from pathlib import Path

CORE_API = Path("src/adultgen/apps/core_api.py")
COLLECTION_ROUTER = Path("src/adultgen/api/routers/collections.py")
COLLECTION_SERVICE = Path("src/adultgen/services/collections.py")
COLLECTION_CLIENT = Path("apps/mini_app/src/collection.ts")


def test_core_api_registers_collection_router() -> None:
    content = CORE_API.read_text()

    assert "collections" in content
    assert "collections.router" in content


def test_collection_router_exposes_list_save_unsave_endpoints() -> None:
    content = COLLECTION_ROUTER.read_text()

    assert "/saved" in content
    assert "@router.put" in content
    assert "@router.delete" in content
    assert "get_current_token_claims" in content


def test_collection_service_checks_active_publication_and_filters_deleted() -> None:
    content = COLLECTION_SERVICE.read_text()

    assert "PublicationStatus.ACTIVE" in content
    assert "Publication.deleted_at.is_(None)" in content
    assert "SavedPublication" in content


def test_mini_app_collection_client_calls_backend_endpoints() -> None:
    content = COLLECTION_CLIENT.read_text()

    assert "/collections/saved" in content
    assert "PUT" in content
    assert "DELETE" in content
    assert "Authorization" in content
