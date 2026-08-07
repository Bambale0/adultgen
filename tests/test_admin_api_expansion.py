from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_admin_router_exposes_core_admin_surfaces() -> None:
    admin_router = read("src/adultgen/api/routers/admin.py")

    assert '"/users"' in admin_router
    assert '"/users/{user_id}/capabilities"' in admin_router
    assert '"/generations"' in admin_router
    assert '"/publications"' in admin_router
    assert '"/publications/{publication_id}/actions"' in admin_router
    assert '"/payments/orders"' in admin_router
    assert '"/wallet/adjustments"' in admin_router
    assert '"/audit/events"' in admin_router
    assert "require_admin_api_token" in admin_router


def test_admin_service_uses_audit_and_existing_wallet_ledger() -> None:
    service = read("src/adultgen/services/admin.py")

    assert "record_admin_audit_event" in service
    assert "WalletEntryType.ADMIN_ADJUSTMENT" in service
    assert "credit_wallet(" in service
    assert "PublicationStatus.HIDDEN.value" in service
    assert "PublicationStatus.DELETED.value" in service
    assert "update_user_capabilities" in service
    assert "wallet_adjustment_credit" in service


def test_admin_audit_actor_is_nullable_for_static_token_auth() -> None:
    audit_model = read("src/adultgen/db/models/audit.py")
    service = read("src/adultgen/services/admin.py")

    assert "admin_user_id: Mapped[uuid.UUID | None]" in audit_model
    assert "admin_user_id=admin_user_id," in service
    assert "00000000-0000-0000-0000-000000000000" not in service


def test_admin_schemas_cover_lists_and_mutations() -> None:
    schemas = read("src/adultgen/api/schemas/admin.py")

    assert "AdminUserCapabilityUpdateRequest" in schemas
    assert "AdminPublicationActionRequest" in schemas
    assert "AdminWalletAdjustmentRequest" in schemas
    assert "AdminAuditEventResponse" in schemas
    assert 'Literal["hide", "restore", "delete"]' in schemas
    assert 'Literal["purchased", "subscription", "bonus"]' in schemas
