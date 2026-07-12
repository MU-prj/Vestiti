"""Tests for the worker scaffold (no Redis connection required)."""

import asyncio

from camerino_worker.main import WorkerSettings, ping


def test_ping_task_returns_pong() -> None:
    assert asyncio.run(ping({})) == "pong"


def test_worker_settings_register_tasks() -> None:
    assert ping in WorkerSettings.functions
