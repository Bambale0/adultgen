from pathlib import Path

ROUTER_TS = Path("src/adultgen/api/routers/adult_consent.py")
APP_TSX = Path("apps/mini_app/src/App.tsx")
CONSENT_TS = Path("apps/mini_app/src/adultConsent.ts")
ENV_EXAMPLE = Path(".env.example")


def test_backend_adult_consent_routes_exist() -> None:
    content = ROUTER_TS.read_text()

    assert "@router.get" in content
    assert "@router.post" in content
    assert "/accept" in content
    assert "get_current_token_claims" in content


def test_frontend_feed_route_uses_adult_gate() -> None:
    content = APP_TSX.read_text()

    assert "requiresAdultConsent" in content
    assert "AdultGate" in content
    assert "acceptAdultConsent" in content
    assert "fetchAdultConsentStatus" in content


def test_frontend_adult_consent_client_calls_backend() -> None:
    content = CONSENT_TS.read_text()

    assert "/adult-consent" in content
    assert "/adult-consent/accept" in content
    assert "Authorization" in content


def test_env_documents_adult_policy_version() -> None:
    assert "ADULT_POLICY_VERSION" in ENV_EXAMPLE.read_text()
