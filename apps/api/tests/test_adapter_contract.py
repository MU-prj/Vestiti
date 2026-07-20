"""Contract test: every SourceAdapter yields valid, well-attributed products.

Any new adapter must be added to the ADAPTERS registry below; the contract
is what the ingestion pipeline relies on.
"""

from collections.abc import Callable

import pytest
from adapter_fixtures import (
    build_affiliate_csv_adapter,
    build_affiliate_xml_adapter,
    build_google_tsv_adapter,
    build_google_xml_adapter,
    build_shopify_adapter,
)

from camerino_api.adapters.mock import default_fixture_adapters
from camerino_domain import Availability, Product, SourceAdapter

pytestmark = pytest.mark.anyio

ADAPTERS: dict[str, Callable[[], SourceAdapter]] = {
    "mock": lambda: default_fixture_adapters()[0],
    "shopify": build_shopify_adapter,
    "google_xml": build_google_xml_adapter,
    "google_tsv": build_google_tsv_adapter,
    "affiliate_csv": build_affiliate_csv_adapter,
    "affiliate_xml": build_affiliate_xml_adapter,
}


@pytest.fixture(params=sorted(ADAPTERS))
def adapter(request: pytest.FixtureRequest) -> SourceAdapter:
    factory = ADAPTERS[request.param]
    return factory()


async def test_adapter_yields_at_least_one_product(adapter: SourceAdapter) -> None:
    products = [product async for product in adapter.fetch_products()]
    assert products


async def test_adapter_products_satisfy_the_contract(adapter: SourceAdapter) -> None:
    async for product in adapter.fetch_products():
        assert isinstance(product, Product)
        assert product.source_id == adapter.source_id
        assert product.price.amount > 0
        assert isinstance(product.availability, Availability)
        assert product.product_url.startswith(("http://", "https://"))
        if product.affiliate_url is not None:
            assert product.affiliate_url.startswith(("http://", "https://"))
        assert product.raw, "raw payload must be preserved for replay/debugging"


async def test_adapter_is_replayable(adapter: SourceAdapter) -> None:
    """Two consecutive fetches yield the same product ids (determinism in CI)."""
    first = [product.id async for product in adapter.fetch_products()]
    second = [product.id async for product in adapter.fetch_products()]
    assert first == second
