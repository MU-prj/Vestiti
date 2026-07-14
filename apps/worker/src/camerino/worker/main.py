"""ARQ worker entrypoint.

Job functions are registered here as phases land (ingestion, watches, try-on).
"""

import os
from typing import Any, ClassVar

from arq.connections import RedisSettings


async def ping(ctx: dict[str, Any]) -> str:
    """Trivial job used to verify the worker loop end to end."""
    return "pong"


def redis_settings_from_env() -> RedisSettings:
    """Build Redis settings from the REDIS_URL environment variable."""
    return RedisSettings.from_dsn(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))


class WorkerSettings:
    """ARQ worker configuration (`arq camerino.worker.main.WorkerSettings`)."""

    functions: ClassVar = [ping]
    redis_settings = redis_settings_from_env()
