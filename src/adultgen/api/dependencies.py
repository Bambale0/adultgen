"""FastAPI dependency providers."""

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
