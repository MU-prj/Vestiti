"""FastAPI application entrypoint.

Exposes the health endpoints required by the deployment environment;
feature routers are mounted here as phases land.
"""

from fastapi import FastAPI


def create_app() -> FastAPI:
    """Build the FastAPI application (app factory pattern, test friendly)."""
    app = FastAPI(title="Camerino API", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        """Liveness probe: the process is up."""
        return {"status": "ok"}

    @app.get("/ready")
    def ready() -> dict[str, str]:
        """Readiness probe: the app can serve traffic.

        Dependency checks (DB, Redis) are added when those services land.
        """
        return {"status": "ready"}

    return app


app = create_app()
