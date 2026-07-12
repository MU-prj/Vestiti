"""canonical products and offers

Revision ID: 0001
Revises:
Create Date: 2026-07-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "canonical_products",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("key_kind", sa.String(length=16), nullable=False),
        sa.Column("key_value", sa.Text(), nullable=False),
        sa.Column("brand", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("image_url", sa.Text(), nullable=False),
        sa.Column("category", sa.Text(), nullable=True),
        sa.Column("color_hex", sa.String(length=7), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("key_kind", "key_value", name="uq_canonical_identity"),
    )
    op.create_table(
        "offers",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column(
            "canonical_product_id",
            sa.String(length=36),
            sa.ForeignKey("canonical_products.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_id", sa.Text(), nullable=False),
        sa.Column("price_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("price_currency", sa.String(length=3), nullable=False),
        sa.Column("availability", sa.String(length=16), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("raw", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'")),
        sa.UniqueConstraint("canonical_product_id", "source_id", name="uq_offer_per_source"),
    )
    op.create_index("ix_offers_canonical_product_id", "offers", ["canonical_product_id"])


def downgrade() -> None:
    op.drop_index("ix_offers_canonical_product_id", table_name="offers")
    op.drop_table("offers")
    op.drop_table("canonical_products")
