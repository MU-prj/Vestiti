"""Worker configuration tests (no Redis required)."""

from camerino.worker.main import WorkerSettings, ping, redis_settings_from_env


async def test_ping_job_returns_pong() -> None:
    assert await ping({}) == "pong"


def test_worker_settings_registers_ping() -> None:
    assert ping in WorkerSettings.functions


def test_redis_settings_default_dsn() -> None:
    settings = redis_settings_from_env()
    assert settings.port == 6379
