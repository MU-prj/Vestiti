"""Tests for the ingestion pipeline against an in-memory store."""

from datetime import UTC, datetime

import pytest

from camerino_api.adapters.mock import default_fixture_adapters
from camerino_api.ingestion import IngestionService
from camerino_domain import CanonicalProduct, IdentityKey, IdentityKind, Offer

pytestmark = pytest.mark.anyio

NOW = datetime(2026, 7, 12, 12, 0, tzinfo=UTC)


class InMemoryProductStore:
    """Minimal ProductStore double for pipeline unit tests."""

    def __init__(self) -> None:
        self.canonicals: dict[IdentityKey, CanonicalProduct] = {}
        self.offers: dict[tuple[str, str], Offer] = {}

    async def get_by_key(self, key: IdentityKey) -> CanonicalProduct | None:
        return self.canonicals.get(key)

    async def add_canonical(self, canonical: CanonicalProduct) -> None:
        self.canonicals[canonical.key] = canonical

    async def upsert_offer(self, offer: Offer, *, raw: dict[str, object]) -> None:
        self.offers[(offer.canonical_product_id, offer.source_id)] = offer


async def test_same_gtin_across_stores_collapses_into_one_canonical() -> None:
    """DoD fase 1: due offer con lo stesso GTIN -> un CanonicalProduct."""
    store = InMemoryProductStore()
    service = IngestionService(store)
    store_a, store_b = default_fixture_adapters()

    report_a = await service.ingest(store_a, now=NOW)
    report_b = await service.ingest(store_b, now=NOW)

    assert report_a.products_seen == 2
    assert report_a.canonicals_created == 2
    assert report_b.products_seen == 2
    # The shared-GTIN sneaker must reuse store A's canonical.
    assert report_b.canonicals_created == 1
    assert len(store.canonicals) == 3

    gtin_keys = [key for key in store.canonicals if key.kind is IdentityKind.GTIN]
    assert len(gtin_keys) == 1
    canonical = store.canonicals[gtin_keys[0]]
    shared_offers = [offer for (cid, _), offer in store.offers.items() if cid == canonical.id]
    assert {offer.source_id for offer in shared_offers} == {
        "mock-store-a",
        "mock-store-b",
    }
    prices = {offer.final_price.amount for offer in shared_offers}
    assert len(prices) == 2


async def test_reingesting_the_same_source_updates_offers_in_place() -> None:
    store = InMemoryProductStore()
    service = IngestionService(store)
    store_a, _ = default_fixture_adapters()

    await service.ingest(store_a, now=NOW)
    later = datetime(2026, 7, 13, 12, 0, tzinfo=UTC)
    report = await service.ingest(store_a, now=later)

    assert report.canonicals_created == 0
    assert len(store.offers) == 2
    assert all(offer.last_seen_at == later for offer in store.offers.values())
