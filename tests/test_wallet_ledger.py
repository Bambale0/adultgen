import pytest

from adultgen.domain.enums import CreditBucket, WalletEntryType
from adultgen.domain.wallet_ledger import (
    LedgerEntrySnapshot,
    WalletLedgerError,
    allocate_available_credits,
    allocate_reserved_credits,
    project_wallet_balances,
)


def test_wallet_projection_tracks_available_and_reserved_balances() -> None:
    balances = project_wallet_balances(
        [
            LedgerEntrySnapshot(
                WalletEntryType.BONUS_CREDIT,
                CreditBucket.BONUS,
                20,
            ),
            LedgerEntrySnapshot(
                WalletEntryType.PAYMENT_CREDIT,
                CreditBucket.PURCHASED,
                100,
            ),
            LedgerEntrySnapshot(
                WalletEntryType.GENERATION_RESERVE,
                CreditBucket.BONUS,
                15,
            ),
            LedgerEntrySnapshot(
                WalletEntryType.GENERATION_RESERVE,
                CreditBucket.PURCHASED,
                35,
            ),
        ]
    )

    assert balances.available_by_bucket[CreditBucket.BONUS] == 5
    assert balances.available_by_bucket[CreditBucket.PURCHASED] == 65
    assert balances.reserved_by_bucket[CreditBucket.BONUS] == 15
    assert balances.reserved_by_bucket[CreditBucket.PURCHASED] == 35
    assert balances.total_available == 70
    assert balances.total_reserved == 50


def test_available_allocation_uses_bonus_then_subscription_then_purchased() -> None:
    balances = project_wallet_balances(
        [
            LedgerEntrySnapshot(WalletEntryType.BONUS_CREDIT, CreditBucket.BONUS, 10),
            LedgerEntrySnapshot(
                WalletEntryType.SUBSCRIPTION_CREDIT,
                CreditBucket.SUBSCRIPTION,
                20,
            ),
            LedgerEntrySnapshot(WalletEntryType.PAYMENT_CREDIT, CreditBucket.PURCHASED, 100),
        ]
    )

    allocations = allocate_available_credits(balances, 45)

    assert [(item.bucket, item.amount) for item in allocations] == [
        (CreditBucket.BONUS, 10),
        (CreditBucket.SUBSCRIPTION, 20),
        (CreditBucket.PURCHASED, 15),
    ]


def test_reserved_allocation_uses_same_bucket_order() -> None:
    balances = project_wallet_balances(
        [
            LedgerEntrySnapshot(WalletEntryType.BONUS_CREDIT, CreditBucket.BONUS, 10),
            LedgerEntrySnapshot(
                WalletEntryType.SUBSCRIPTION_CREDIT,
                CreditBucket.SUBSCRIPTION,
                20,
            ),
            LedgerEntrySnapshot(WalletEntryType.PAYMENT_CREDIT, CreditBucket.PURCHASED, 100),
            LedgerEntrySnapshot(WalletEntryType.GENERATION_RESERVE, CreditBucket.BONUS, 10),
            LedgerEntrySnapshot(
                WalletEntryType.GENERATION_RESERVE,
                CreditBucket.SUBSCRIPTION,
                20,
            ),
            LedgerEntrySnapshot(
                WalletEntryType.GENERATION_RESERVE,
                CreditBucket.PURCHASED,
                15,
            ),
        ]
    )

    allocations = allocate_reserved_credits(balances, 35)

    assert [(item.bucket, item.amount) for item in allocations] == [
        (CreditBucket.BONUS, 10),
        (CreditBucket.SUBSCRIPTION, 20),
        (CreditBucket.PURCHASED, 5),
    ]


def test_charge_reserved_reduces_reserved_without_returning_available() -> None:
    balances = project_wallet_balances(
        [
            LedgerEntrySnapshot(WalletEntryType.PAYMENT_CREDIT, CreditBucket.PURCHASED, 100),
            LedgerEntrySnapshot(
                WalletEntryType.GENERATION_RESERVE,
                CreditBucket.PURCHASED,
                40,
            ),
            LedgerEntrySnapshot(
                WalletEntryType.GENERATION_CHARGE,
                CreditBucket.PURCHASED,
                40,
            ),
        ]
    )

    assert balances.total_available == 60
    assert balances.total_reserved == 0


def test_release_reserved_returns_credits_to_available() -> None:
    balances = project_wallet_balances(
        [
            LedgerEntrySnapshot(WalletEntryType.PAYMENT_CREDIT, CreditBucket.PURCHASED, 100),
            LedgerEntrySnapshot(
                WalletEntryType.GENERATION_RESERVE,
                CreditBucket.PURCHASED,
                40,
            ),
            LedgerEntrySnapshot(
                WalletEntryType.GENERATION_RELEASE,
                CreditBucket.PURCHASED,
                40,
            ),
        ]
    )

    assert balances.total_available == 100
    assert balances.total_reserved == 0


def test_allocation_rejects_insufficient_available_balance() -> None:
    balances = project_wallet_balances(
        [LedgerEntrySnapshot(WalletEntryType.PAYMENT_CREDIT, CreditBucket.PURCHASED, 10)]
    )

    with pytest.raises(WalletLedgerError, match="Insufficient available"):
        allocate_available_credits(balances, 11)
