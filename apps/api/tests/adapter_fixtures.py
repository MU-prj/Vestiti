"""Builders for adapters under test, wired to recorded fixtures.

No adapter built here performs live network calls: HTTP-based adapters get
an httpx.MockTransport that replays the recorded responses (VCR-style).
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx

from camerino_api.adapters.affiliate import AWIN_MAPPING, AffiliateFeedAdapter
from camerino_api.adapters.google_shopping import GoogleShoppingFeedAdapter
from camerino_api.adapters.shopify import ShopifyStorefrontAdapter

FIXTURES = Path(__file__).parent / "fixtures"


def fixture_text(name: str) -> str:
    return (FIXTURES / name).read_text()


def shopify_transport() -> httpx.MockTransport:
    """Replays the two recorded Storefront pages, keyed on the GraphQL cursor."""
    page1 = json.loads(fixture_text("shopify_products_page1.json"))
    page2 = json.loads(fixture_text("shopify_products_page2.json"))

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        cursor = body.get("variables", {}).get("after")
        return httpx.Response(200, json=page2 if cursor == "cursor-page-1" else page1)

    return httpx.MockTransport(handler)


def build_shopify_adapter() -> ShopifyStorefrontAdapter:
    return ShopifyStorefrontAdapter(
        source_id="shopify-boutique",
        shop_domain="boutique.example.com",
        storefront_token="test-token-not-a-secret",
        client=httpx.AsyncClient(transport=shopify_transport()),
    )


def build_google_xml_adapter() -> GoogleShoppingFeedAdapter:
    return GoogleShoppingFeedAdapter.from_content(
        source_id="google-feed-xml",
        content=fixture_text("google_shopping_feed.xml"),
        feed_format="xml",
    )


def build_google_tsv_adapter() -> GoogleShoppingFeedAdapter:
    return GoogleShoppingFeedAdapter.from_content(
        source_id="google-feed-tsv",
        content=fixture_text("google_shopping_feed.tsv"),
        feed_format="tsv",
    )


def build_affiliate_csv_adapter() -> AffiliateFeedAdapter:
    return AffiliateFeedAdapter.from_content(
        source_id="awin-partner",
        content=fixture_text("awin_feed.csv"),
        mapping=AWIN_MAPPING,
        feed_format="csv",
    )


def build_affiliate_xml_adapter() -> AffiliateFeedAdapter:
    return AffiliateFeedAdapter.from_content(
        source_id="awin-partner-xml",
        content=fixture_text("affiliate_feed.xml"),
        mapping=AWIN_MAPPING,
        feed_format="xml",
    )
