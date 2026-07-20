"""Shopify Storefront API adapter (GraphQL, cursor pagination).

Uses only the official Storefront API with a merchant-provided token
(hard invariant #1: no scraping). In CI the HTTP layer is replaced by an
httpx.MockTransport replaying recorded fixtures.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from decimal import Decimal
from typing import Any

import httpx

from camerino_domain import Availability, Money, Product

PRODUCTS_QUERY = """
query Products($first: Int!, $after: String) {
  products(first: $first, after: $after) {
    edges {
      node {
        id
        handle
        title
        description
        vendor
        onlineStoreUrl
        featuredImage { url }
        variants(first: 1) {
          edges {
            node {
              sku
              barcode
              availableForSale
              price { amount currencyCode }
            }
          }
        }
      }
    }
    pageInfo { hasNextPage endCursor }
  }
}
"""


class ShopifyStorefrontAdapter:
    """SourceAdapter over the Shopify Storefront GraphQL API."""

    def __init__(
        self,
        source_id: str,
        shop_domain: str,
        storefront_token: str,
        *,
        api_version: str = "2024-10",
        page_size: int = 50,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._source_id = source_id
        self._shop_domain = shop_domain
        self._token = storefront_token
        self._endpoint = f"https://{shop_domain}/api/{api_version}/graphql.json"
        self._page_size = page_size
        self._client = client
        self.skipped_records = 0

    @property
    def source_id(self) -> str:
        return self._source_id

    async def fetch_products(self) -> AsyncIterator[Product]:
        client = self._client or httpx.AsyncClient()
        owns_client = self._client is None
        self.skipped_records = 0
        try:
            cursor: str | None = None
            while True:
                payload = {
                    "query": PRODUCTS_QUERY,
                    "variables": {"first": self._page_size, "after": cursor},
                }
                response = await client.post(
                    self._endpoint,
                    json=payload,
                    headers={"X-Shopify-Storefront-Access-Token": self._token},
                )
                response.raise_for_status()
                connection = response.json()["data"]["products"]
                for edge in connection["edges"]:
                    product = self._to_product(edge["node"])
                    if product is None:
                        self.skipped_records += 1
                        continue
                    yield product
                page_info = connection["pageInfo"]
                if not page_info["hasNextPage"]:
                    break
                cursor = page_info["endCursor"]
        finally:
            if owns_client:
                await client.aclose()

    def _to_product(self, node: dict[str, Any]) -> Product | None:
        variant_edges = node.get("variants", {}).get("edges", [])
        if not variant_edges:
            return None
        variant = variant_edges[0]["node"]
        image = node.get("featuredImage") or {}
        product_url = (
            node.get("onlineStoreUrl")
            or f"https://{self._shop_domain}/products/{node.get('handle', '')}"
        )
        try:
            return Product(
                id=f"{self._source_id}:{node['id']}",
                brand=node.get("vendor") or "",
                title=node.get("title") or "",
                description=node.get("description") or "",
                price=Money(
                    Decimal(variant["price"]["amount"]),
                    variant["price"]["currencyCode"],
                ),
                availability=(
                    Availability.IN_STOCK
                    if variant.get("availableForSale")
                    else Availability.OUT_OF_STOCK
                ),
                image_url=image.get("url") or "",
                product_url=product_url,
                source_id=self._source_id,
                gtin=variant.get("barcode") or None,
                sku=variant.get("sku") or None,
                raw=node,
            )
        except (KeyError, ValueError, ArithmeticError):
            return None
