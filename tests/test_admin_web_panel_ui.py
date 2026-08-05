from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_admin_panel_is_standalone_entrypoint() -> None:
    main = read("apps/web_app/src/main.tsx")

    assert "import { AdminPanel } from './AdminPanel';" in main
    assert "window.location.pathname === '/admin'" in main
    assert "<AdminPanel />" in main
    assert "<App />" in main
    assert "./admin.css" in main


def test_admin_panel_has_professional_workspace_sections() -> None:
    panel = read("apps/web_app/src/AdminPanel.tsx")

    assert "AdultGen Admin" in panel
    assert "Control Room" in panel
    assert "type AdminTab" in panel
    assert "'overview' | 'users' | 'generations' | 'publications' | 'payments' | 'wallet' | 'audit'" in panel
    assert "AdminOverview" in panel
    assert "AdminUsersSection" in panel
    assert "AdminGenerationsSection" in panel
    assert "AdminPublicationsSection" in panel
    assert "AdminPaymentsSection" in panel
    assert "AdminWalletSection" in panel
    assert "AdminAuditSection" in panel


def test_admin_panel_keeps_token_and_dangerous_actions_separate() -> None:
    panel = read("apps/web_app/src/AdminPanel.tsx")

    assert "adultgen_admin_token" in panel
    assert "localStorage.setItem(ADMIN_TOKEN_STORAGE_KEY" in panel
    assert "localStorage.removeItem(ADMIN_TOKEN_STORAGE_KEY)" in panel
    assert "reason" in panel
    assert "updateAdminUserCapabilities" in panel
    assert "applyAdminPublicationAction" in panel
    assert "createAdminWalletAdjustment" in panel
    assert "fetchAdminAuditEvents" in panel


def test_admin_css_isolated_from_user_styles() -> None:
    css = read("apps/web_app/src/admin.css")

    assert ".admin-shell" in css
    assert ".admin-sidebar" in css
    assert ".admin-main-panel" in css
    assert ".admin-table" in css
    assert ".admin-two-column" in css
    assert "@media (max-width: 1180px)" in css


def test_admin_client_backing_methods_are_used() -> None:
    panel = read("apps/web_app/src/AdminPanel.tsx")
    client = read("apps/web_app/src/adminApi.ts")

    for method in [
        "fetchAdminUsers",
        "fetchAdminGenerations",
        "fetchAdminPublications",
        "fetchAdminPaymentOrders",
        "fetchAdminAuditEvents",
        "updateAdminUserCapabilities",
        "applyAdminPublicationAction",
        "createAdminWalletAdjustment",
    ]:
        assert method in panel
        assert method in client
