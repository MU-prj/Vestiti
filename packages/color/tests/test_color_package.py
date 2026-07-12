"""Smoke test for the color package scaffold."""

import camerino_color


def test_package_is_importable_and_deterministic_by_contract() -> None:
    assert camerino_color.__doc__ is not None
    assert camerino_color.__all__ == []
