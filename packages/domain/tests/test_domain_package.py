"""Smoke test for the domain package: exports exist and stay I/O-free."""

import subprocess
import sys

import camerino_domain

FORBIDDEN_INFRA_MODULES = ("fastapi", "sqlalchemy", "httpx", "arq", "redis")


def test_package_exports_the_domain_surface() -> None:
    assert "Product" in camerino_domain.__all__
    assert "ProductDeduplicator" in camerino_domain.__all__


def test_importing_the_domain_pulls_no_infrastructure() -> None:
    """Importing camerino_domain in a fresh interpreter loads no infra libs."""
    probe = (
        "import sys; import camerino_domain; "
        f"loaded = [m for m in {FORBIDDEN_INFRA_MODULES!r} if m in sys.modules]; "
        "assert not loaded, f'domain import loaded {loaded}'"
    )
    subprocess.run([sys.executable, "-c", probe], check=True)
