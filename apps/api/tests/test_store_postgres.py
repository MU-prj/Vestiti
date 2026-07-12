"""Integration tests: ingestion pipeline against a real PostgreSQL.

These run whenever DATABASE_URL points at a reachable PostgreSQL (the CI
test job provides a service container) and skip cleanly otherwise.
"""

import os

import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from camerino_api.adapters.mock import default_fixture_adapters
from camerino_api.db.engine import create_session_factory
from camerino_api.db.models import Base
from camerino_api.db.store import SqlAlchemyProductStore
from camerino_api.ingestion import IngestionService
from camerino_domain import IdentityKey, IdentityKind

pytestmark = pytest.mark.anyio

DATABASE_URL = os.environ.get("DATABASE_URL")


async def _postgres_reachable(url: str) -> bool:
    engine = create_async_engine(url)
    try:
        async with engine.connect():
            return True
    except OSError:
        return False
    finally:
        await engine.dispose()


@pytest.fixture
async def engine() -> AsyncEngine:  # type: ignore[misc]
    if DATABASE_URL is None or not DATABASE_URL.startswith("postgresql+asyncpg"):
        pytest.skip("DATABASE_URL does not point at an asyncpg PostgreSQL")
    if not await _postgres_reachable(DATABASE_URL):
        pytest.skip("PostgreSQL is not reachable from this environment")
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    await engine.dispose()


async def test_ingestion_round_trip_collapses_shared_gtin(engine: AsyncEngine) -> None:
    """DoD fase 1 su Postgres: stesso GTIN da due negozi -> un canonical, due offer."""
    session_factory = create_session_factory(engine)
    store_a, store_b = default_fixture_adapters()

    async with session_factory() as session, session.begin():
        service = IngestionService(SqlAlchemyProductStore(session))
        await service.ingest(store_a)
        await service.ingest(store_b)

    # The fixture stores share GTIN 0885909950805, normalized to 14 digits.
    key = IdentityKey(IdentityKind.GTIN, ("00885909950805",))

    async with session_factory() as session:
        store = SqlAlchemyProductStore(session)
        canonical = await store.get_by_key(key)
        assert canonical is not None
        offers = await store.offers_for(canonical.id)
        assert {offer.source_id for offer in offers} == {"mock-store-a", "mock-store-b"}


async def test_reingestion_is_idempotent_on_offers(engine: AsyncEngine) -> None:
    session_factory = create_session_factory(engine)
    store_a, _ = default_fixture_adapters()

    async with session_factory() as session, session.begin():
        service = IngestionService(SqlAlchemyProductStore(session))
        first = await service.ingest(store_a)
    async with session_factory() as session, session.begin():
        service = IngestionService(SqlAlchemyProductStore(session))
        second = await service.ingest(store_a)

    assert first.canonicals_created == 2
    assert second.canonicals_created == 0
    assert second.offers_upserted == first.offers_upserted
