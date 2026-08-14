from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_google_auth_verifies_server_side_identity_token() -> None:
    integration = (ROOT / "src/adultgen/integrations/google_auth.py").read_text(encoding="utf-8")
    router = (ROOT / "src/adultgen/api/routers/auth.py").read_text(encoding="utf-8")

    assert "verify_oauth2_token" in integration
    assert "email_verified" in integration
    assert '@router.post("/google"' in router
    assert "payload.credential" in router


def test_unverified_email_session_endpoint_is_removed() -> None:
    router = (ROOT / "src/adultgen/api/routers/auth.py").read_text(encoding="utf-8")
    assert '@router.post("/web-session"' not in router
    assert '@router.post("/telegram-login"' in router
