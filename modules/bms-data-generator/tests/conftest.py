"""Shared fixtures for `bms-data-generator` tests.

Heavy parts (the vendor scenario runner) are replaced by tiny fakes so unit
and integration tests stay fast and deterministic.
"""

from __future__ import annotations

import threading
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from bms_data_generator.api.control import get_service as get_control_service
from bms_data_generator.api.datasets import get_service as get_dump_service


class _FakeRunResult:
    def __init__(self, points: int = 1) -> None:
        self.points_emitted = points


class _FakeRunner:
    def __init__(self, release: threading.Event | None = None) -> None:
        self._release = release

    def run(self) -> list[_FakeRunResult]:
        if self._release is not None:
            self._release.wait(timeout=2.0)
        return [_FakeRunResult(1)]


def _make_runner_factory(release: threading.Event):
    def _factory(_path: Path):
        return _FakeRunner(release), object()

    return _factory


def _make_dump_factory():
    def _factory(job):
        job.output_path.write_text("# fake dump\n", encoding="utf-8")
        return [_FakeRunResult(1)]

    return _factory


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    from bms_data_generator.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
def reset_services():
    """Reset singletons and inject lightweight factories before every test."""
    runner = get_control_service()
    dumper = get_dump_service()

    runner.reset()
    dumper.reset()

    release = threading.Event()
    release.set()  # default: don't block
    runner.set_runner_factory(_make_runner_factory(release))
    dumper.set_runner_factory(_make_dump_factory())

    yield

    runner.reset()
    dumper.reset()


@pytest.fixture
def existing_yaml(tmp_path: Path) -> Path:
    """A minimal existing YAML so config-path validation in services succeeds."""
    p = tmp_path / "scenario.yaml"
    p.write_text("project: {}\n", encoding="utf-8")
    return p


@pytest.fixture
def block_runner():
    """Pause the fake runner so tests can observe the busy/active state."""
    release = threading.Event()
    runner = get_control_service()
    runner.set_runner_factory(_make_runner_factory(release))
    yield release
    release.set()
