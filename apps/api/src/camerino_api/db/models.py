"""SQLAlchemy ORM models.

Canonical products and offers persist the domain dedup result: one
``canonical_products`` row per identity key, N ``offers`` rows (one per
source) pointing at it.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base for all Camerino tables."""


class CanonicalProductRow(Base):
    __tablename__ = "canonical_products"
    __table_args__ = (UniqueConstraint("key_kind", "key_value", name="uq_canonical_identity"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    key_kind: Mapped[str] = mapped_column(String(16))
    key_value: Mapped[str] = mapped_column(Text)
    brand: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    image_url: Mapped[str] = mapped_column(Text)
    category: Mapped[str | None] = mapped_column(Text, nullable=True)
    color_hex: Mapped[str | None] = mapped_column(String(7), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    offers: Mapped[list[OfferRow]] = relationship(
        back_populates="canonical_product", cascade="all, delete-orphan"
    )


class OfferRow(Base):
    __tablename__ = "offers"
    __table_args__ = (
        UniqueConstraint("canonical_product_id", "source_id", name="uq_offer_per_source"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    canonical_product_id: Mapped[str] = mapped_column(
        ForeignKey("canonical_products.id", ondelete="CASCADE")
    )
    source_id: Mapped[str] = mapped_column(Text)
    price_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    price_currency: Mapped[str] = mapped_column(String(3))
    availability: Mapped[str] = mapped_column(String(16))
    url: Mapped[str] = mapped_column(Text)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    raw: Mapped[dict[str, object]] = mapped_column(JSONB, default=dict)

    canonical_product: Mapped[CanonicalProductRow] = relationship(back_populates="offers")
