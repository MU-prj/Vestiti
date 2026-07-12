"""SQLAlchemy implementation of the domain ProductStore port."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from camerino_api.db.models import CanonicalProductRow, OfferRow
from camerino_domain import (
    Availability,
    CanonicalProduct,
    IdentityKey,
    Money,
    Offer,
)

_KEY_SEPARATOR = "\x1f"  # unit separator: never appears in normalized key parts


def encode_key_value(key: IdentityKey) -> str:
    return _KEY_SEPARATOR.join(key.value)


class SqlAlchemyProductStore:
    """ProductStore backed by PostgreSQL through an AsyncSession."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_key(self, key: IdentityKey) -> CanonicalProduct | None:
        stmt = select(CanonicalProductRow).where(
            CanonicalProductRow.key_kind == key.kind.value,
            CanonicalProductRow.key_value == encode_key_value(key),
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            return None
        return CanonicalProduct(
            id=row.id,
            key=key,
            brand=row.brand,
            title=row.title,
            description=row.description,
            image_url=row.image_url,
            category=row.category,
            color_hex=row.color_hex,
        )

    async def add_canonical(self, canonical: CanonicalProduct) -> None:
        self._session.add(
            CanonicalProductRow(
                id=canonical.id,
                key_kind=canonical.key.kind.value,
                key_value=encode_key_value(canonical.key),
                brand=canonical.brand,
                title=canonical.title,
                description=canonical.description,
                image_url=canonical.image_url,
                category=canonical.category,
                color_hex=canonical.color_hex,
                created_at=datetime.now(tz=UTC),
            )
        )
        await self._session.flush()

    async def upsert_offer(self, offer: Offer, *, raw: dict[str, object]) -> None:
        stmt = select(OfferRow).where(
            OfferRow.canonical_product_id == offer.canonical_product_id,
            OfferRow.source_id == offer.source_id,
        )
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            row = OfferRow(
                id=str(uuid4()),
                canonical_product_id=offer.canonical_product_id,
                source_id=offer.source_id,
            )
            self._session.add(row)
        row.price_amount = offer.final_price.amount
        row.price_currency = offer.final_price.currency
        row.availability = offer.availability.value
        row.url = offer.url
        row.last_seen_at = offer.last_seen_at
        row.raw = raw
        await self._session.flush()

    async def offers_for(self, canonical_product_id: str) -> list[Offer]:
        """Read back the offers of a canonical product (test/reporting helper)."""
        stmt = select(OfferRow).where(OfferRow.canonical_product_id == canonical_product_id)
        rows = (await self._session.execute(stmt)).scalars().all()
        return [
            Offer(
                canonical_product_id=row.canonical_product_id,
                source_id=row.source_id,
                final_price=Money(row.price_amount, row.price_currency),
                availability=Availability(row.availability),
                url=row.url,
                last_seen_at=row.last_seen_at,
            )
            for row in rows
        ]


__all__ = ["SqlAlchemyProductStore", "encode_key_value"]
