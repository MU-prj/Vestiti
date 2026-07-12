"""Ingestion tasks: run mock sources through the pipeline into Postgres."""

from __future__ import annotations

from typing import Any

from camerino_api.adapters.mock import default_fixture_adapters
from camerino_api.db.engine import create_engine, create_session_factory
from camerino_api.db.store import SqlAlchemyProductStore
from camerino_api.ingestion import IngestionService


async def ingest_mock_sources(ctx: dict[Any, Any]) -> dict[str, int]:
    """Ingest the two fixture mock stores; returns counters for observability."""
    engine = create_engine()
    session_factory = create_session_factory(engine)
    totals = {"products_seen": 0, "canonicals_created": 0, "offers_upserted": 0}
    try:
        async with session_factory() as session, session.begin():
            service = IngestionService(SqlAlchemyProductStore(session))
            for adapter in default_fixture_adapters():
                report = await service.ingest(adapter)
                totals["products_seen"] += report.products_seen
                totals["canonicals_created"] += report.canonicals_created
                totals["offers_upserted"] += report.offers_upserted
    finally:
        await engine.dispose()
    return totals
