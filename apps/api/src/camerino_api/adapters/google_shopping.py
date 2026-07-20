"""Google Shopping feed adapter: RSS 2.0 XML (g: namespace) and TSV.

Feeds are official merchant exports (hard invariant #1). Content comes
from an injected async loader so tests replay recorded fixtures and the
live path fetches over HTTPS with httpx.
"""

from __future__ import annotations

import csv
import io
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Literal

import httpx
from defusedxml.ElementTree import fromstring as parse_untrusted_xml

from camerino_api.adapters.parsing import parse_availability, parse_price
from camerino_domain import Product

FeedFormat = Literal["xml", "tsv"]
_G_NS = "{http://base.google.com/ns/1.0}"

_REQUIRED_FIELDS = ("id", "title", "link", "image_link", "brand", "price", "availability")


class GoogleShoppingFeedAdapter:
    """SourceAdapter over a Google Shopping product feed."""

    def __init__(
        self,
        source_id: str,
        loader: Callable[[], Awaitable[str]],
        feed_format: FeedFormat,
    ) -> None:
        self._source_id = source_id
        self._loader = loader
        self._format: FeedFormat = feed_format
        self.skipped_records = 0

    @classmethod
    def from_content(
        cls, source_id: str, content: str, feed_format: FeedFormat
    ) -> GoogleShoppingFeedAdapter:
        async def loader() -> str:
            return content

        return cls(source_id, loader, feed_format)

    @classmethod
    def from_url(
        cls,
        source_id: str,
        url: str,
        feed_format: FeedFormat,
        client: httpx.AsyncClient | None = None,
    ) -> GoogleShoppingFeedAdapter:
        async def loader() -> str:
            http = client or httpx.AsyncClient()
            try:
                response = await http.get(url)
                response.raise_for_status()
                return response.text
            finally:
                if client is None:
                    await http.aclose()

        return cls(source_id, loader, feed_format)

    @property
    def source_id(self) -> str:
        return self._source_id

    async def fetch_products(self) -> AsyncIterator[Product]:
        content = await self._loader()
        self.skipped_records = 0
        records = _parse_xml(content) if self._format == "xml" else _parse_tsv(content)
        for record in records:
            product = self._to_product(record)
            if product is None:
                self.skipped_records += 1
                continue
            yield product

    def _to_product(self, record: dict[str, str]) -> Product | None:
        if any(not record.get(field, "").strip() for field in _REQUIRED_FIELDS):
            return None
        price = parse_price(record["price"])
        availability = parse_availability(record["availability"])
        if price is None or availability is None:
            return None
        try:
            return Product(
                id=record["id"],
                brand=record["brand"],
                title=record["title"],
                description=record.get("description", ""),
                price=price,
                availability=availability,
                image_url=record["image_link"],
                product_url=record["link"],
                source_id=self._source_id,
                gtin=record.get("gtin") or None,
                mpn=record.get("mpn") or None,
                category=record.get("google_product_category") or None,
                raw=dict(record),
            )
        except ValueError:
            return None


def _parse_xml(content: str) -> list[dict[str, str]]:
    root = parse_untrusted_xml(content)
    records: list[dict[str, str]] = []
    for item in root.iter("item"):
        record: dict[str, str] = {}
        for child in item:
            tag = child.tag.removeprefix(_G_NS)
            record[tag] = (child.text or "").strip()
        records.append(record)
    return records


def _parse_tsv(content: str) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(content), delimiter="\t")
    return [
        {key: (value or "").strip() for key, value in row.items() if key is not None}
        for row in reader
    ]
