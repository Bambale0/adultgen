"""FastAPI dependency providers."""

from collections.abc import AsyncIterator
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from adultgen.config import Settings, get_settings
from adultgen.db.session import Database


@lru_cache(maxsize=1)
def get_database() -> Database:
    """Return the process-wide database wrapper."""

    return Database(get_settings())


async def get_db_session(
    database: Database = Depends(get_database),
) -> AsyncIterator[AsyncSession]:
    """Yield a transactional SQLAlchemy session for one API request."""

    async with database.session() as session:
        yield session


def get_runtime_settings() -> Settings:
    """Dependency wrapper around cached settings."""

    return get_settings()
