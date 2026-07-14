"""Ingestion pipeline tests (SQLite in-memory; PostgreSQL in migrations.yml)."""

from collections.abc import Iterator
from dataclasses import replace
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from camerino.adapters.mock import MockSourceAdapter, fixture_catalog
from camerino.api.db import Base
from camerino.api.models import CanonicalProductRow, OfferRow
from camerino.api.services.ingestion import IngestStats, ingest_product, ingest_source
from camerino.domain import Money

NOW = datetime(2026, 7, 14, 12, 0, tzinfo=UTC)


@pytest.fixture
def session() -> Iterator[Session]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db_session:
        yield db_session
    engine.dispose()


async def test_two_shops_same_gtin_collapse_into_one_canonical(session: Session) -> None:
    """DoD phase 1: offers sharing a GTIN collapse into one CanonicalProduct."""
    stats_a = await ingest_source(session, MockSourceAdapter("shop-a"), now=NOW)
    stats_b = await ingest_source(
        session,
        MockSourceAdapter("shop-b", fixture_catalog("shop-b", price_offset_minor=-1500)),
        now=NOW,
    )
    session.commit()

    assert stats_a.canonicals_created == 3
    assert stats_b.canonicals_created == 0  # every shop-b product matched shop-a's
    canonicals = session.scalars(select(CanonicalProductRow)).all()
    offers = session.scalars(select(OfferRow)).all()
    assert len(canonicals) == 3
    assert len(offers) == 6

    coat = session.scalars(
        select(CanonicalProductRow).where(CanonicalProductRow.gtin == "04006381333931")
    ).one()
    coat_prices = sorted(offer.price_minor for offer in coat.offers)
    assert coat_prices == [18400, 19900]


async def test_reingestion_updates_offers_without_duplicating(session: Session) -> None:
    await ingest_source(session, MockSourceAdapter("shop-a"), now=NOW)
    later = datetime(2026, 7, 15, 12, 0, tzinfo=UTC)
    updated_catalog = [
        product
        if product.id != "coat-navy"
        else replace(product, price=Money(amount_minor=14900, currency="EUR"))
        for product in fixture_catalog("shop-a")
    ]
    stats = await ingest_source(session, MockSourceAdapter("shop-a", updated_catalog), now=later)
    session.commit()

    assert stats.offers_created == 0
    assert stats.offers_updated == 3
    offers = session.scalars(select(OfferRow)).all()
    assert len(offers) == 3
    coat_offer = session.scalars(select(OfferRow).where(OfferRow.external_id == "coat-navy")).one()
    assert coat_offer.price_minor == 14900


async def test_fuzzy_match_rejected_on_conflicting_gtin(session: Session) -> None:
    catalog = fixture_catalog("shop-a")
    coat = catalog[0]
    await ingest_source(session, MockSourceAdapter("shop-a", [coat]), now=NOW)

    # Same brand/title/color but a different valid GTIN: must NOT merge.
    conflicting = replace(
        coat,
        id="coat-navy-v2",
        source_id="shop-b",
        gtin="4006381333818",
        mpn=None,
        product_url="https://shop-b.example.com/products/coat-navy",
    )
    stats = IngestStats()
    ingest_product(session, conflicting, now=NOW, stats=stats)
    session.commit()

    assert stats.canonicals_created == 1
    assert len(session.scalars(select(CanonicalProductRow)).all()) == 2


async def test_offer_metadata_is_persisted(session: Session) -> None:
    await ingest_source(session, MockSourceAdapter("shop-a"), now=NOW)
    session.commit()

    scarf = session.scalars(select(OfferRow).where(OfferRow.external_id == "scarf-sage")).one()
    assert scarf.availability == "out_of_stock"
    assert scarf.currency == "EUR"
    assert scarf.canonical.brand == "Verde"
    assert scarf.canonical.gtin is None
    assert scarf.canonical.brand_sku_key is not None
