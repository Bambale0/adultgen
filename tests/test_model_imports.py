import adultgen.db.models  # noqa: F401
from adultgen.db.base import Base


def test_orm_metadata_contains_core_tables() -> None:
    expected_tables = {
        "users",
        "telegram_channels",
        "wallets",
        "wallet_entries",
        "payment_orders",
        "payment_webhook_raw",
        "media_assets",
        "projects",
        "scenes",
        "generation_tasks",
        "publications",
        "partner_payout_requests",
        "admin_audit_events",
    }

    assert expected_tables.issubset(set(Base.metadata.tables))
