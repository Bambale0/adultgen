"""Wallet API schemas."""

from __future__ import annotations

from pydantic import BaseModel


class WalletBucketBalanceResponse(BaseModel):
    """Projected balance for one credit bucket."""

    bucket: str
    available: int
    reserved: int


class WalletBalanceResponse(BaseModel):
    """Current wallet balance projected from the immutable ledger."""

    currency: str
    total_available: int
    total_reserved: int
    total_balance: int
    buckets: list[WalletBucketBalanceResponse]
