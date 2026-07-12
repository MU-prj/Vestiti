"""Shared fixtures for API tests."""

import pytest


@pytest.fixture
def anyio_backend() -> str:
    """Run anyio-marked async tests on asyncio only."""
    return "asyncio"
