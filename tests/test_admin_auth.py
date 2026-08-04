from fastapi.testclient import TestClient

from adultgen.apps.core_api import create_app
from adultgen.config import get_settings


def test_admin_health_rejects_missing_token(monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_API_TOKEN", "secret-admin")
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.get("/admin/health")

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing admin bearer token."


def test_admin_health_rejects_wrong_token(monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_API_TOKEN", "secret-admin")
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.get(
        "/admin/health",
        headers={"Authorization": "Bearer wrong"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid admin bearer token."


def test_admin_health_accepts_valid_token(monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_API_TOKEN", "secret-admin")
    get_settings.cache_clear()
    client = TestClient(create_app())

    response = client.get(
        "/admin/health",
        headers={"Authorization": "Bearer secret-admin"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "scope": "admin"}
