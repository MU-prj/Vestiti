"""Camerino API application entrypoint."""

from fastapi import FastAPI

app = FastAPI(title="Camerino API", version="0.1.0")


@app.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe: the process is up and serving requests."""
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> dict[str, str]:
    """Readiness probe.

    Dependency checks (database, redis, object storage) are wired in as the
    corresponding integrations land in later phases.
    """
    return {"status": "ready"}
