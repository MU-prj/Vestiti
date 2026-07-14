"""Database engine and session plumbing."""

import os
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Declarative base for all Camerino ORM models."""


def database_url() -> str:
    """Read the database URL from the environment."""
    return os.environ.get(
        "DATABASE_URL", "postgresql+psycopg://camerino:camerino@localhost:5432/camerino"
    )


def make_engine(url: str | None = None) -> Engine:
    """Create an engine for the given (or environment-configured) URL."""
    return create_engine(url or database_url())


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create a session factory bound to the engine."""
    return sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def session_scope(factory: sessionmaker[Session]) -> Iterator[Session]:
    """Provide a transactional scope: commit on success, rollback on error."""
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
