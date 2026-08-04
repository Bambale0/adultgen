from adultgen.db import models  # noqa: F401
from adultgen.db.base import Base


def test_notification_delivery_table_is_registered() -> None:
    assert "notification_deliveries" in Base.metadata.tables
