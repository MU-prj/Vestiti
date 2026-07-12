"""Smoke test for the domain package scaffold."""

import camerino_domain


def test_package_is_importable_and_io_free() -> None:
    assert camerino_domain.__doc__ is not None
    assert camerino_domain.__all__ == []
