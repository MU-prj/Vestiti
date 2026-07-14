"""Offer: one shop's listing of a canonical product."""

from dataclasses import dataclass
from datetime import datetime

from camerino.domain.money import Money
from camerino.domain.product import Availability


@dataclass(slots=True)
class Offer:
    """A purchasable listing of a canonical product at one source.

    The pair (`source_id`, `url`) identifies the offer within a canonical
    product; price and availability are updated on each ingestion pass.
    """

    source_id: str
    url: str
    price: Money
    availability: Availability
    affiliate_url: str | None
    first_seen_at: datetime
    last_seen_at: datetime
