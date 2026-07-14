"""MockSourceAdapter tests."""

from camerino.adapters.mock import MockSourceAdapter, fixture_catalog
from camerino.adapters.source import SourceAdapter
from camerino.domain import Product


async def test_mock_adapter_is_a_source_adapter() -> None:
    adapter = MockSourceAdapter("shop-a")
    assert isinstance(adapter, SourceAdapter)
    assert adapter.source_id == "shop-a"


async def test_mock_adapter_yields_the_fixture_catalog() -> None:
    adapter = MockSourceAdapter("shop-a")
    products = [product async for product in adapter.fetch()]
    assert products == fixture_catalog("shop-a")
    assert all(isinstance(product, Product) for product in products)
    assert all(product.source_id == "shop-a" for product in products)


async def test_two_mock_shops_share_gtins_for_dedup_scenarios() -> None:
    catalog_a = fixture_catalog("shop-a")
    catalog_b = fixture_catalog("shop-b", price_offset_minor=-1500)
    gtins_a = {product.gtin for product in catalog_a if product.gtin}
    gtins_b = {product.gtin for product in catalog_b if product.gtin}
    assert gtins_a == gtins_b
    assert catalog_a[0].price.amount_minor - catalog_b[0].price.amount_minor == 1500


async def test_mock_adapter_accepts_an_explicit_catalog() -> None:
    products = fixture_catalog("shop-x")[:1]
    adapter = MockSourceAdapter("shop-x", products=products)
    assert [product async for product in adapter.fetch()] == products
