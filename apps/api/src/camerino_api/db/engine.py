"""Async engine and session factory, configured from the environment."""

from __future__ import annotations

import os

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

DEFAULT_DATABASE_URL = "postgresql+asyncpg://camerino:camerino-dev-only@localhost:5432/camerino"


def database_url() -> str:
    """Resolve the database URL from the environment."""
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


def create_engine(url: str | None = None) -> AsyncEngine:
    return create_async_engine(url or database_url())


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)
