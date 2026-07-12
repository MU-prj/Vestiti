"""Camerino domain package.

Pure, framework-free domain entities and services. Nothing in this package
may import FastAPI, SQLAlchemy, or any other infrastructure dependency:
all logic here must be I/O-free and fully testable with fixtures.

Entities land in phase 1 (Product, ProductIdentity, Offer, Collection,
Outfit, User, SkinProfile, Watch, TryOnJob).
"""

__all__: list[str] = []
