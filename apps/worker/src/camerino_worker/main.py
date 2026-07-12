"""Camerino ARQ worker entrypoint.

Run with: `arq camerino_worker.main.WorkerSettings`.
Real jobs (ingestion, watches, try-on orchestration) land in later phases.
"""

import os
from collections.abc import Awaitable, Callable
from typing import Any, ClassVar

from arq.connections import RedisSettings


async def ping(ctx: dict[Any, Any]) -> str:
    """Trivial task used to verify worker wiring end to end."""
    return "pong"


class WorkerSettings:
    """ARQ worker settings: task registry and Redis connection."""

    functions: ClassVar[list[Callable[..., Awaitable[Any]]]] = [ping]
    redis_settings = RedisSettings.from_dsn(os.environ.get("REDIS_URL", "redis://localhost:6379/0"))
