"""Tests for the mock source adapter."""

import pytest

from camerino_api.adapters.mock import MockSourceAdapter, default_fixture_adapters
from camerino_domain import Product

pytestmark = pytest.mark.anyio


async def test_mock_adapter_yields_its_fixture_products() -> None:
    store_a, _ = default_fixture_adapters()
    products = [product async for product in store_a.fetch_products()]
    assert len(products) == 2
    assert all(isinstance(product, Product) for product in products)
    assert all(product.source_id == store_a.source_id for product in products)


async def test_mock_adapter_rejects_products_from_other_sources() -> None:
    store_a, _ = default_fixture_adapters()
    foreign = [product async for product in store_a.fetch_products()]
    with pytest.raises(ValueError, match="belongs to"):
        MockSourceAdapter("another-store", foreign)


async def test_default_fixtures_share_one_gtin_across_stores() -> None:
    store_a, store_b = default_fixture_adapters()
    gtins_a = {p.gtin async for p in store_a.fetch_products() if p.gtin}
    gtins_b = {p.gtin.lstrip("0") async for p in store_b.fetch_products() if p.gtin}
    assert any(gtin.lstrip("0") in gtins_b for gtin in gtins_a)
