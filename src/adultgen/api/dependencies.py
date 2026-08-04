"""FastAPI dependency providers."""

from __future__ import annotations

import hmac
from collections.abc import AsyncIterator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.config import Settings, get_settings
from adultgen.db.session import Database
from adultgen.security.tokens import AccessTokenClaims, TokenError, verify_access_token


@lru_cache(maxsize=1)
def get_database() -> Database:
    """Return the process-wide database wrapper."""

    return Database(get_settings())


async def get_db_session(
    database: Annotated[Database, Depends(get_database)],
) -> AsyncIterator[AsyncSession]:
    """Yield a transactional SQLAlchemy session for one API request."""

    async with database.session() as session:
        yield session


def get_runtime_settings() -> Settings:
    """Dependency wrapper around cached settings."""

    return get_settings()


def get_current_token_claims(
    settings: Annotated[Settings, Depends(get_runtime_settings)],
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> AccessTokenClaims:
    """Verify Authorization: Bearer token and return access-token claims."""

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
        )

    token = authorization.removeprefix("Bearer ").strip()
    try:
        return verify_access_token(token, secret=settings.jwt_secret)
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


def require_admin_api_token(
    settings: Annotated[Settings, Depends(get_runtime_settings)],
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> None:
    """Require static admin bearer token for early admin endpoints."""

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing admin bearer token.",
        )

    token = authorization.removeprefix("Bearer ").strip()
    if not hmac.compare_digest(token, settings.admin_api_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin bearer token.",
        )
