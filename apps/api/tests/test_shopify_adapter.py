"""Tests for the Shopify Storefront adapter (recorded fixtures, no live calls)."""

import pytest
from adapter_fixtures import build_shopify_adapter

from camerino_domain import Availability

pytestmark = pytest.mark.anyio


async def test_paginates_through_all_storefront_pages() -> None:
    adapter = build_shopify_adapter()
    products = [product async for product in adapter.fetch_products()]
    assert [p.title for p in products] == [
        "Air Max 90 White",
        "Wool Overshirt",
        "Linen Shirt",
    ]


async def test_maps_variant_fields_onto_the_product() -> None:
    adapter = build_shopify_adapter()
    products = {p.title: p async for p in adapter.fetch_products()}

    sneaker = products["Air Max 90 White"]
    assert sneaker.brand == "Nike"
    assert sneaker.gtin == "0885909950805"
    assert sneaker.sku == "AM90-WHT-42"
    assert str(sneaker.price.amount) == "139.99"
    assert sneaker.price.currency == "EUR"
    assert sneaker.availability is Availability.IN_STOCK
    assert sneaker.product_url == "https://boutique.example.com/products/air-max-90-white"

    overshirt = products["Wool Overshirt"]
    assert overshirt.availability is Availability.OUT_OF_STOCK
    assert overshirt.gtin is None
    # Without onlineStoreUrl the adapter builds the canonical /products/<handle> URL.
    assert overshirt.product_url == "https://boutique.example.com/products/wool-overshirt"


async def test_product_ids_are_namespaced_by_source() -> None:
    adapter = build_shopify_adapter()
    async for product in adapter.fetch_products():
        assert product.id.startswith("shopify-boutique:")
