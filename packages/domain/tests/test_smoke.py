"""Smoke test: the domain package is importable."""

from camerino import domain


def test_domain_package_importable() -> None:
    assert domain.__version__
