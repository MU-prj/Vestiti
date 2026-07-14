"""Smoke test: the adapters package is importable."""

from camerino import adapters


def test_adapters_package_importable() -> None:
    assert adapters.__version__
