"""Wallet ledger application service."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.db.models.wallets import Wallet, WalletEntry
from adultgen.domain.enums import CreditBucket, WalletEntryType
from adultgen.domain.wallet_ledger import (
    BucketAllocation,
    LedgerEntrySnapshot,
    WalletBalances,
    allocate_available_credits,
    allocate_reserved_credits,
    project_wallet_balances,
)


async def get_or_create_wallet(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    currency: str = "credits",
) -> Wallet:
    """Return a locked user wallet, creating it when missing."""

    await session.execute(
        insert(Wallet)
        .values(user_id=user_id, currency=currency)
        .on_conflict_do_nothing(index_elements=[Wallet.user_id])
    )
    result = await session.execute(
        select(Wallet).where(Wallet.user_id == user_id).with_for_update()
    )
    return result.scalar_one()


async def project_wallet_from_db(session: AsyncSession, *, wallet_id: uuid.UUID) -> WalletBalances:
    """Project wallet balances from persisted append-only entries."""

    result = await session.execute(
        select(WalletEntry).where(WalletEntry.wallet_id == wallet_id).order_by(WalletEntry.created_at)
    )
    entries = [
        LedgerEntrySnapshot(
            entry_type=WalletEntryType(entry.entry_type),
            bucket=CreditBucket(entry.bucket),
            amount=entry.amount,
        )
        for entry in result.scalars()
    ]
    return project_wallet_balances(entries)


async def credit_wallet(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    amount: int,
    bucket: CreditBucket,
    entry_type: WalletEntryType,
    operation_id: uuid.UUID,
    payment_order_id: uuid.UUID | None = None,
    reason: str | None = None,
) -> WalletBalances:
    """Append a credit/refund/admin entry and update cached balances."""

    wallet = await get_or_create_wallet(session, user_id=user_id)
    await _append_entry(
        session,
        wallet_id=wallet.id,
        operation_id=operation_id,
        entry_type=entry_type,
        bucket=bucket,
        amount=amount,
        payment_order_id=payment_order_id,
        reason=reason,
    )
    return await _refresh_cached_balances(session, wallet)


async def reserve_credits(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    amount: int,
    operation_id: uuid.UUID,
    generation_task_id: uuid.UUID | None = None,
    reason: str | None = None,
) -> WalletBalances:
    """Move credits from available to reserved buckets."""

    wallet = await get_or_create_wallet(session, user_id=user_id)
    balances = await project_wallet_from_db(session, wallet_id=wallet.id)
    allocations = allocate_available_credits(balances, amount)
    await _append_allocated_entries(
        session,
        wallet_id=wallet.id,
        operation_id=operation_id,
        entry_type=WalletEntryType.GENERATION_RESERVE,
        allocations=allocations,
        generation_task_id=generation_task_id,
        reason=reason,
    )
    return await _refresh_cached_balances(session, wallet)


async def charge_reserved_credits(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    amount: int,
    operation_id: uuid.UUID,
    generation_task_id: uuid.UUID | None = None,
    reason: str | None = None,
) -> WalletBalances:
    """Finalize a generation charge from reserved credits."""

    wallet = await get_or_create_wallet(session, user_id=user_id)
    balances = await project_wallet_from_db(session, wallet_id=wallet.id)
    allocations = allocate_reserved_credits(balances, amount)
    await _append_allocated_entries(
        session,
        wallet_id=wallet.id,
        operation_id=operation_id,
        entry_type=WalletEntryType.GENERATION_CHARGE,
        allocations=allocations,
        generation_task_id=generation_task_id,
        reason=reason,
    )
    return await _refresh_cached_balances(session, wallet)


async def release_reserved_credits(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    amount: int,
    operation_id: uuid.UUID,
    generation_task_id: uuid.UUID | None = None,
    reason: str | None = None,
) -> WalletBalances:
    """Return reserved credits back to available after failure/refund."""

    wallet = await get_or_create_wallet(session, user_id=user_id)
    balances = await project_wallet_from_db(session, wallet_id=wallet.id)
    allocations = allocate_reserved_credits(balances, amount)
    await _append_allocated_entries(
        session,
        wallet_id=wallet.id,
        operation_id=operation_id,
        entry_type=WalletEntryType.GENERATION_RELEASE,
        allocations=allocations,
        generation_task_id=generation_task_id,
        reason=reason,
    )
    return await _refresh_cached_balances(session, wallet)


async def _append_allocated_entries(
    session: AsyncSession,
    *,
    wallet_id: uuid.UUID,
    operation_id: uuid.UUID,
    entry_type: WalletEntryType,
    allocations: list[BucketAllocation],
    generation_task_id: uuid.UUID | None,
    reason: str | None,
) -> None:
    for allocation in allocations:
        await _append_entry(
            session,
            wallet_id=wallet_id,
            operation_id=operation_id,
            entry_type=entry_type,
            bucket=allocation.bucket,
            amount=allocation.amount,
            generation_task_id=generation_task_id,
            reason=reason,
        )


async def _append_entry(
    session: AsyncSession,
    *,
    wallet_id: uuid.UUID,
    operation_id: uuid.UUID,
    entry_type: WalletEntryType,
    bucket: CreditBucket,
    amount: int,
    generation_task_id: uuid.UUID | None = None,
    payment_order_id: uuid.UUID | None = None,
    reason: str | None = None,
) -> None:
    session.add(
        WalletEntry(
            wallet_id=wallet_id,
            operation_id=operation_id,
            entry_type=entry_type.value,
            bucket=bucket.value,
            amount=amount,
            generation_task_id=generation_task_id,
            payment_order_id=payment_order_id,
            reason=reason,
        )
    )
    await session.flush()


async def _refresh_cached_balances(session: AsyncSession, wallet: Wallet) -> WalletBalances:
    balances = await project_wallet_from_db(session, wallet_id=wallet.id)
    wallet.cached_available_balance = balances.total_available
    wallet.cached_reserved_balance = balances.total_reserved
    await session.flush()
    return balances
