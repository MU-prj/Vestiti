"""Mock source adapter emitting fixture products (used in CI and dev).

Two default sources deliberately share a GTIN so the ingestion pipeline
demonstrably collapses them into one canonical product with two offers.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence

from camerino_domain import Availability, ColorRef, Money, Product


class MockSourceAdapter:
    """A SourceAdapter that yields a fixed list of fixture products."""

    def __init__(self, source_id: str, products: Sequence[Product]) -> None:
        self._source_id = source_id
        self._products = list(products)
        for product in self._products:
            if product.source_id != source_id:
                msg = f"product {product.id} belongs to {product.source_id}, not {source_id}"
                raise ValueError(msg)

    @property
    def source_id(self) -> str:
        return self._source_id

    async def fetch_products(self) -> AsyncIterator[Product]:
        for product in self._products:
            yield product


def default_fixture_adapters() -> tuple[MockSourceAdapter, MockSourceAdapter]:
    """Two mock shops with one overlapping garment (same GTIN, prices differ)."""
    shared_gtin = "0885909950805"
    store_a = MockSourceAdapter(
        "mock-store-a",
        [
            Product(
                id="a-airmax90",
                brand="Nike",
                title="Air Max 90 White",
                description="Iconic runner in white leather.",
                price=Money.of("139.99", "EUR"),
                availability=Availability.IN_STOCK,
                image_url="https://cdn.example.com/a/airmax90.jpg",
                product_url="https://store-a.example.com/airmax90",
                source_id="mock-store-a",
                gtin=shared_gtin,
                color_primary=ColorRef("#f5f5f0", name="white"),
                category="Apparel & Accessories > Shoes",
                raw={"feed_id": "a-1"},
            ),
            Product(
                id="a-trench",
                brand="Burberry",
                title="Heritage Trench Coat",
                description="Double-breasted cotton gabardine trench.",
                price=Money.of("1890.00", "EUR"),
                availability=Availability.IN_STOCK,
                image_url="https://cdn.example.com/a/trench.jpg",
                product_url="https://store-a.example.com/trench",
                source_id="mock-store-a",
                mpn="BB-TRENCH-HER",
                color_primary=ColorRef("#c8a165", name="honey"),
                category="Apparel & Accessories > Clothing > Outerwear",
                raw={"feed_id": "a-2"},
            ),
        ],
    )
    store_b = MockSourceAdapter(
        "mock-store-b",
        [
            Product(
                id="b-airmax90",
                brand="Nike",
                title="Nike Air Max 90 - White",
                description="Air Max 90, white colourway.",
                price=Money.of("129.00", "EUR"),
                availability=Availability.IN_STOCK,
                image_url="https://cdn.example.com/b/airmax90.jpg",
                product_url="https://store-b.example.com/nike-air-max-90",
                source_id="mock-store-b",
                gtin=f"0{shared_gtin}",
                color_primary=ColorRef("#ffffff", name="white"),
                category="Apparel & Accessories > Shoes",
                raw={"feed_id": "b-1"},
            ),
            Product(
                id="b-scarf",
                brand="Acne Studios",
                title="Canada Wool Scarf",
                description="Oversized fringed wool scarf.",
                price=Money.of("180.00", "EUR"),
                availability=Availability.OUT_OF_STOCK,
                image_url="https://cdn.example.com/b/scarf.jpg",
                product_url="https://store-b.example.com/canada-scarf",
                source_id="mock-store-b",
                sku="AS-CANADA-PINK",
                color_primary=ColorRef("#e8b4c8", name="pale pink"),
                category="Apparel & Accessories > Clothing Accessories > Scarves",
                raw={"feed_id": "b-2"},
            ),
        ],
    )
    return store_a, store_b
