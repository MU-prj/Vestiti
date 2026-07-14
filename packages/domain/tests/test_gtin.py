"""GTIN normalization and checksum tests."""

import pytest

from camerino.domain.identity import normalize_gtin

# 4006381333931 is a well-known valid EAN-13 (Stabilo Boss).
VALID_EAN13 = "4006381333931"


def test_valid_ean13_is_zero_padded_to_gtin14() -> None:
    assert normalize_gtin(VALID_EAN13) == "04006381333931"


def test_valid_upc12_is_accepted() -> None:
    # 036000291452 is a canonical valid UPC-A example.
    assert normalize_gtin("036000291452") == "00036000291452"


def test_separators_and_whitespace_are_stripped() -> None:
    assert normalize_gtin(" 4006381-333931 ") == "04006381333931"


def test_invalid_checksum_returns_none() -> None:
    assert normalize_gtin("4006381333932") is None


@pytest.mark.parametrize("value", ["", "abc", "123", "12345678901234567"])
def test_invalid_lengths_return_none(value: str) -> None:
    assert normalize_gtin(value) is None
