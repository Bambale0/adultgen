"""Wallet balance API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.api.dependencies import get_current_token_claims, get_db_session
from adultgen.api.schemas.wallets import WalletBalanceResponse, WalletBucketBalanceResponse
from adultgen.domain.enums import CreditBucket
from adultgen.security.tokens import AccessTokenClaims
from adultgen.services.wallets import get_or_create_wallet, project_wallet_from_db

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.get("/me", response_model=WalletBalanceResponse)
async def get_my_wallet_balance(
    claims: Annotated[AccessTokenClaims, Depends(get_current_token_claims)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> WalletBalanceResponse:
    """Return the current user's projected wallet balance."""

    wallet = await get_or_create_wallet(session, user_id=claims.subject)
    balances = await project_wallet_from_db(session, wallet_id=wallet.id)
    buckets = [
        WalletBucketBalanceResponse(
            bucket=bucket.value,
            available=balances.available_by_bucket.get(bucket, 0),
            reserved=balances.reserved_by_bucket.get(bucket, 0),
        )
        for bucket in CreditBucket
    ]
    return WalletBalanceResponse(
        currency=wallet.currency,
        total_available=balances.total_available,
        total_reserved=balances.total_reserved,
        total_balance=balances.total_available + balances.total_reserved,
        buckets=buckets,
    )
