from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_admin_router_exposes_core_support_surfaces() -> None:
    router = read("src/adultgen/api/routers/admin.py")

    assert '@router.get("/users"' in router
    assert '@router.get("/users/{user_id}"' in router
    assert '@router.patch("/users/{user_id}/flags"' in router
    assert '@router.get("/generations"' in router
    assert '@router.get("/publications"' in router
    assert '@router.patch("/publications/{publication_id}/status"' in router
    assert '@router.get("/payments/orders"' in router
    assert '@router.post("/wallet-adjustments"' in router
    assert '@router.get("/audit-events"' in router
    assert "require_admin_api_token" in router


def test_admin_router_records_audit_for_dangerous_actions() -> None:
    router = read("src/adultgen/api/routers/admin.py")

    assert "record_admin_audit_event" in router
    assert 'action="patch_user_flags"' in router
    assert 'action="patch_publication_status"' in router
    assert 'action="wallet_adjustment"' in router
    assert "before_state=" in router
    assert "after_state=" in router


def test_admin_wallet_adjustment_uses_existing_ledger() -> None:
    router = read("src/adultgen/api/routers/admin.py")
    wallet_service = read("src/adultgen/services/wallets.py")

    assert "WalletEntryType.ADMIN_ADJUSTMENT" in router
    assert "CreditBucket(payload.bucket)" in router
    assert "credit_wallet(" in router
    assert "admin_user_id=payload.admin_user_id" in router
    assert "admin_user_id: uuid.UUID | None = None" in wallet_service
    assert "admin_user_id=admin_user_id" in wallet_service
    assert "cached_available_balance" not in router


def test_admin_audit_model_supports_static_admin_token_until_identity_exists() -> None:
    model = read("src/adultgen/db/models/audit.py")
    service = read("src/adultgen/services/admin_audit.py")

    assert "admin_user_id: Mapped[uuid.UUID | None]" in model
    assert "record_admin_audit_event" in service
    assert "before_state or {}" in service
    assert "after_state or {}" in service


def test_admin_schemas_are_typed_for_dashboard_consumers() -> None:
    schemas = read("src/adultgen/api/schemas/admin.py")

    assert "class AdminUserResponse" in schemas
    assert "class AdminGenerationResponse" in schemas
    assert "class AdminPublicationResponse" in schemas
    assert "class AdminPaymentOrderResponse" in schemas
    assert "class AdminWalletAdjustmentRequest" in schemas
    assert "class AdminAuditEventResponse" in schemas
    assert "reason: str = Field(min_length=3, max_length=500)" in schemas


def test_web_admin_client_targets_new_admin_endpoints() -> None:
    client = read("apps/web_app/src/adminApi.ts")

    assert "fetchAdminUsers" in client
    assert "patchAdminUserFlags" in client
    assert "fetchAdminGenerations" in client
    assert "fetchAdminPublications" in client
    assert "patchAdminPublicationStatus" in client
    assert "fetchAdminPaymentOrders" in client
    assert "createAdminWalletAdjustment" in client
    assert "fetchAdminAuditEvents" in client
    assert "Authorization" in client
