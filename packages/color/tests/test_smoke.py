"""Smoke test: the color package is importable."""

from camerino import color


def test_color_package_importable() -> None:
    assert color.__version__
