from fastapi.testclient import TestClient

from adultgen.apps.core_api import create_app
from adultgen.config import get_settings


REQUIRED_TEST_ENV = {
    "DATABASE_URL": "postgresql+asyncpg://adultgen:adultgen@localhost:5432/adultgen",
    "REDIS_URL": "redis://localhost:6379/0",
    "S3_ENDPOINT_URL": "http://localhost:9000",
    "S3_ACCESS_KEY": "test",
    "S3_SECRET_KEY": "test",
    "TELEGRAM_DEFAULT_WEBHOOK_SECRET": "test-webhook-secret",
    "TELEGRAM_DEFAULT_BOT_TOKEN": "123456:test",
    "KIE_API_KEY": "test-kie-key",
    "KIE_CALLBACK_URL": "https://example.com/webhooks/kie",
    "BILLING_BASE_URL": "https://pay.example.com",
    "SHARPAY_API_KEY": "test-sharpay",
    "CROCOPAY_API_KEY": "test-crocopay",
    "CROCOPAY_SECRET": "test-crocopay-secret",
    "JWT_SECRET": "test-jwt-secret",
}


def _prepare_admin_test_env(monkeypatch, *, admin_token: str = "secret-admin") -> None:
    for key, value in REQUIRED_TEST_ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("ADMIN_API_TOKEN", admin_token)
    get_settings.cache_clear()


def test_admin_health_rejects_missing_token(monkeypatch) -> None:
    _prepare_admin_test_env(monkeypatch)
    client = TestClient(create_app())

    response = client.get("/admin/health")

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing admin bearer token."


def test_admin_health_rejects_wrong_token(monkeypatch) -> None:
    _prepare_admin_test_env(monkeypatch)
    client = TestClient(create_app())

    response = client.get(
        "/admin/health",
        headers={"Authorization": "Bearer wrong"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Invalid admin bearer token."


def test_admin_health_accepts_valid_token(monkeypatch) -> None:
    _prepare_admin_test_env(monkeypatch)
    client = TestClient(create_app())

    response = client.get(
        "/admin/health",
        headers={"Authorization": "Bearer secret-admin"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "scope": "admin"}
