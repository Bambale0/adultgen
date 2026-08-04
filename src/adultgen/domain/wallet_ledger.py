"""Pure wallet ledger projection and allocation rules."""

from __future__ import annotations

from dataclasses import dataclass, field

from adultgen.domain.enums import CreditBucket, WalletEntryType

SPEND_BUCKET_ORDER = (
    CreditBucket.BONUS,
    CreditBucket.SUBSCRIPTION,
    CreditBucket.PURCHASED,
)


class WalletLedgerError(ValueError):
    """Raised when a wallet operation would produce an invalid ledger state."""


@dataclass(frozen=True, slots=True)
class LedgerEntrySnapshot:
    """Minimal immutable ledger entry data needed for balance projection."""

    entry_type: WalletEntryType
    bucket: CreditBucket
    amount: int


@dataclass(frozen=True, slots=True)
class BucketAllocation:
    """Amount allocated from or to a specific credit bucket."""

    bucket: CreditBucket
    amount: int


@dataclass(slots=True)
class WalletBalances:
    """Projected available and reserved balances by bucket."""

    available_by_bucket: dict[CreditBucket, int] = field(default_factory=dict)
    reserved_by_bucket: dict[CreditBucket, int] = field(default_factory=dict)

    @property
    def total_available(self) -> int:
        """Return total available credits."""

        return sum(self.available_by_bucket.values())

    @property
    def total_reserved(self) -> int:
        """Return total reserved credits."""

        return sum(self.reserved_by_bucket.values())


def project_wallet_balances(entries: list[LedgerEntrySnapshot]) -> WalletBalances:
    """Project wallet balances from append-only ledger entries."""

    balances = WalletBalances()
    for entry in entries:
        _apply_entry(balances, entry)

    if balances.total_available < 0:
        raise WalletLedgerError("Projected available balance is negative.")
    if balances.total_reserved < 0:
        raise WalletLedgerError("Projected reserved balance is negative.")
    return balances


def allocate_available_credits(
    balances: WalletBalances,
    amount: int,
) -> list[BucketAllocation]:
    """Allocate credits from available buckets using the product spend order."""

    _validate_positive_amount(amount)
    if balances.total_available < amount:
        raise WalletLedgerError("Insufficient available credits.")

    remaining = amount
    allocations: list[BucketAllocation] = []
    for bucket in SPEND_BUCKET_ORDER:
        if remaining <= 0:
            break
        available = balances.available_by_bucket.get(bucket, 0)
        if available <= 0:
            continue
        allocated = min(available, remaining)
        allocations.append(BucketAllocation(bucket=bucket, amount=allocated))
        remaining -= allocated

    if remaining != 0:
        raise WalletLedgerError("Unable to allocate requested available credits.")
    return allocations


def allocate_reserved_credits(
    balances: WalletBalances,
    amount: int,
) -> list[BucketAllocation]:
    """Allocate credits from reserved buckets using the product spend order."""

    _validate_positive_amount(amount)
    if balances.total_reserved < amount:
        raise WalletLedgerError("Insufficient reserved credits.")

    remaining = amount
    allocations: list[BucketAllocation] = []
    for bucket in SPEND_BUCKET_ORDER:
        if remaining <= 0:
            break
        reserved = balances.reserved_by_bucket.get(bucket, 0)
        if reserved <= 0:
            continue
        allocated = min(reserved, remaining)
        allocations.append(BucketAllocation(bucket=bucket, amount=allocated))
        remaining -= allocated

    if remaining != 0:
        raise WalletLedgerError("Unable to allocate requested reserved credits.")
    return allocations


def _apply_entry(balances: WalletBalances, entry: LedgerEntrySnapshot) -> None:
    if entry.amount == 0:
        raise WalletLedgerError("Wallet entry amount must not be zero.")

    match entry.entry_type:
        case (
            WalletEntryType.PAYMENT_CREDIT
            | WalletEntryType.SUBSCRIPTION_CREDIT
            | WalletEntryType.BONUS_CREDIT
            | WalletEntryType.REFUND
            | WalletEntryType.ADMIN_ADJUSTMENT
        ):
            _add_available(balances, entry.bucket, entry.amount)
        case WalletEntryType.GENERATION_RESERVE:
            _add_available(balances, entry.bucket, -entry.amount)
            _add_reserved(balances, entry.bucket, entry.amount)
        case WalletEntryType.GENERATION_CHARGE:
            _add_reserved(balances, entry.bucket, -entry.amount)
        case WalletEntryType.GENERATION_RELEASE:
            _add_reserved(balances, entry.bucket, -entry.amount)
            _add_available(balances, entry.bucket, entry.amount)
        case WalletEntryType.CHARGEBACK:
            _add_available(balances, entry.bucket, -entry.amount)


def _add_available(balances: WalletBalances, bucket: CreditBucket, amount: int) -> None:
    balances.available_by_bucket[bucket] = balances.available_by_bucket.get(bucket, 0) + amount


def _add_reserved(balances: WalletBalances, bucket: CreditBucket, amount: int) -> None:
    balances.reserved_by_bucket[bucket] = balances.reserved_by_bucket.get(bucket, 0) + amount


def _validate_positive_amount(amount: int) -> None:
    if amount <= 0:
        raise WalletLedgerError("Amount must be positive.")
