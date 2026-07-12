"""Normalized ingestion: pull products from a source, dedup, persist offers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from camerino_domain import (
    CanonicalProduct,
    Offer,
    ProductStore,
    SourceAdapter,
    identity_key,
)


@dataclass(frozen=True, slots=True)
class IngestionReport:
    """What one ingestion run did, for logging and assertions."""

    source_id: str
    products_seen: int
    canonicals_created: int
    offers_upserted: int


class IngestionService:
    """Drives one SourceAdapter run against the product store.

    Identity resolution follows the domain rules (GTIN -> brand+MPN ->
    brand+SKU -> fuzzy): the store is queried by identity key so that
    offers from different sources collapse onto the same canonical
    product across runs, not just within one batch.
    """

    def __init__(self, store: ProductStore) -> None:
        self._store = store

    async def ingest(
        self, adapter: SourceAdapter, *, now: datetime | None = None
    ) -> IngestionReport:
        run_time = now or datetime.now(tz=UTC)
        seen = 0
        created = 0
        upserted = 0
        async for product in adapter.fetch_products():
            seen += 1
            key = identity_key(product)
            canonical = await self._store.get_by_key(key)
            if canonical is None:
                canonical = CanonicalProduct.from_product(key, product)
                await self._store.add_canonical(canonical)
                created += 1
            offer = Offer.from_product(product, canonical.id, run_time)
            await self._store.upsert_offer(offer, raw=product.raw)
            upserted += 1
        return IngestionReport(
            source_id=adapter.source_id,
            products_seen=seen,
            canonicals_created=created,
            offers_upserted=upserted,
        )
