"""Tests for the Shopify Storefront adapter (recorded fixtures, no live calls)."""

import httpx
import pytest
from adapter_fixtures import build_shopify_adapter

from camerino_api.adapters.shopify import ShopifyStorefrontAdapter, ShopifyStorefrontError
from camerino_domain import Availability

pytestmark = pytest.mark.anyio


async def test_paginates_through_all_storefront_pages() -> None:
    adapter = build_shopify_adapter()
    products = [product async for product in adapter.fetch_products()]
    assert [p.title for p in products] == [
        "Air Max 90 White",
        "Wool Overshirt",
        "Linen Shirt",
        "Wool Scarf",
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


async def test_aggregates_availability_and_price_across_variants() -> None:
    """A product is in stock if ANY variant is; price/sku come from the
    cheapest available variant, not blindly from the first one."""
    adapter = build_shopify_adapter()
    products = {p.title: p async for p in adapter.fetch_products()}

    scarf = products["Wool Scarf"]
    # First variant is sold out at 120.00; the second is available at 90.00.
    assert scarf.availability is Availability.IN_STOCK
    assert str(scarf.price.amount) == "90.00"
    assert scarf.sku == "JOE-SCF-GRY"
    assert scarf.gtin == "5000000000055"


async def test_raises_on_graphql_errors_in_a_200_response() -> None:
    """Storefront returns 200 with an errors payload (bad token, throttling):
    the adapter must fail loudly, not crash on data being null."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"errors": [{"message": "Invalid Storefront access token"}], "data": None},
        )

    adapter = ShopifyStorefrontAdapter(
        source_id="shopify-broken",
        shop_domain="broken.example.com",
        storefront_token="bad-token-not-a-secret",
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )
    with pytest.raises(ShopifyStorefrontError, match="Invalid Storefront access token"):
        [product async for product in adapter.fetch_products()]
