"""Tests for the Google Shopping and affiliate feed adapters."""

import httpx
import pytest
from adapter_fixtures import (
    build_affiliate_csv_adapter,
    build_affiliate_xml_adapter,
    build_google_tsv_adapter,
    build_google_xml_adapter,
    fixture_text,
)

from camerino_api.adapters.google_shopping import GoogleShoppingFeedAdapter
from camerino_domain import Availability

pytestmark = pytest.mark.anyio


class TestGoogleShoppingXml:
    async def test_parses_items_and_skips_malformed_records(self) -> None:
        adapter = build_google_xml_adapter()
        products = [p async for p in adapter.fetch_products()]
        assert [p.id for p in products] == ["gs-001", "gs-002", "gs-004"]
        assert adapter.skipped_records == 1

    async def test_maps_google_fields(self) -> None:
        adapter = build_google_xml_adapter()
        products = {p.id: p async for p in adapter.fetch_products()}

        sneaker = products["gs-001"]
        assert sneaker.brand == "Nike"
        assert sneaker.gtin == "0885909950805"
        assert sneaker.mpn == "AM90-WHT"
        assert str(sneaker.price.amount) == "139.99"
        assert sneaker.availability is Availability.IN_STOCK
        assert sneaker.category == "Apparel & Accessories > Shoes"
        assert sneaker.raw["color"] == "white"

        assert products["gs-002"].availability is Availability.OUT_OF_STOCK
        # "EUR 210.00" (currency-first) must parse too.
        loafers = products["gs-004"]
        assert str(loafers.price.amount) == "210.00"
        assert loafers.availability is Availability.PREORDER

    async def test_from_url_fetches_the_feed_over_http(self) -> None:
        content = fixture_text("google_shopping_feed.xml")

        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url == "https://store.example.com/feed.xml"
            return httpx.Response(200, text=content)

        adapter = GoogleShoppingFeedAdapter.from_url(
            source_id="google-feed-http",
            url="https://store.example.com/feed.xml",
            feed_format="xml",
            client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        )
        products = [p async for p in adapter.fetch_products()]
        assert len(products) == 3


class TestGoogleShoppingTsv:
    async def test_tsv_and_xml_agree_on_the_same_catalog(self) -> None:
        xml_products = {p.title: p async for p in build_google_xml_adapter().fetch_products()}
        tsv_adapter = build_google_tsv_adapter()
        tsv_products = {p.title: p async for p in tsv_adapter.fetch_products()}

        assert set(xml_products) == set(tsv_products)
        assert tsv_adapter.skipped_records == 1
        for title, xml_product in xml_products.items():
            tsv_product = tsv_products[title]
            assert tsv_product.price == xml_product.price
            assert tsv_product.availability is xml_product.availability
            assert tsv_product.brand == xml_product.brand


class TestAffiliateCsv:
    async def test_maps_awin_columns_and_skips_broken_rows(self) -> None:
        adapter = build_affiliate_csv_adapter()
        products = {p.title: p async for p in adapter.fetch_products()}

        assert set(products) == {"Air Max 90 White", "Silk Scarf"}
        assert adapter.skipped_records == 1

        sneaker = products["Air Max 90 White"]
        assert sneaker.brand == "Nike"
        assert sneaker.gtin == "0885909950805"
        assert sneaker.sku == "P-501"
        assert str(sneaker.price.amount) == "134.50"
        assert sneaker.availability is Availability.IN_STOCK
        # The affiliate deep link is kept separate from the merchant URL.
        assert sneaker.product_url == "https://partner.example.com/air-max-90"
        assert sneaker.affiliate_url == "https://www.awin1.example.com/pclick?p=501"

        assert products["Silk Scarf"].availability is Availability.OUT_OF_STOCK


class TestAffiliateXml:
    async def test_parses_flat_xml_records_with_the_same_mapping(self) -> None:
        adapter = build_affiliate_xml_adapter()
        products = {p.title: p async for p in adapter.fetch_products()}

        assert set(products) == {"Denim Jacket", "Leather Belt"}
        jacket = products["Denim Jacket"]
        assert jacket.brand == "A.P.C."
        assert jacket.gtin == "5000000000031"
        assert jacket.availability is Availability.IN_STOCK
        assert jacket.affiliate_url == "https://www.awin1.example.com/pclick?p=601"

        belt = products["Leather Belt"]
        assert belt.availability is Availability.OUT_OF_STOCK
        assert belt.gtin is None
