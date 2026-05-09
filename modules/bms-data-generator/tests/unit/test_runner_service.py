"""Unit tests for :class:`RunnerService`.

The vendor runner is replaced with a small blocking factory so the tests stay
in unit territory (no YAML loading, no signal handlers, no dataframe build).
"""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from bms_data_generator.services.runner_service import RunnerService


class _FakeRunResult:
    def __init__(self, points: int) -> None:
        self.points_emitted = points


class _FakeRunner:
    """Fake runner that blocks on ``release_event`` to let tests observe phases."""

    def __init__(self, release_event: threading.Event, points: int = 100) -> None:
        self._release_event = release_event
        self._points = points

    def run(self) -> list[_FakeRunResult]:
        self._release_event.wait(timeout=2.0)
        return [_FakeRunResult(self._points)]


def _factory(release_event: threading.Event):
    def _make(_path: Path):
        return _FakeRunner(release_event), object()

    return _make


@pytest.fixture
def release_event() -> threading.Event:
    return threading.Event()


@pytest.fixture
def existing_yaml(tmp_path: Path) -> Path:
    p = tmp_path / "scenario.yaml"
    p.write_text("project: {}\n", encoding="utf-8")
    return p


@pytest.fixture
def service(release_event: threading.Event) -> RunnerService:
    s = RunnerService(runner_factory=_factory(release_event))
    return s


@pytest.mark.unit
def test_start_creates_job(service: RunnerService, existing_yaml: Path) -> None:
    job_id = service.start(config_path=str(existing_yaml), mode="live", aulas=10, faults=[])
    assert job_id
    st = service.status(job_id)
    assert st["job_id"] == job_id
    assert st["phase"] in {"pending", "running"}


@pytest.mark.unit
def test_stop_unknown_job_raises(service: RunnerService) -> None:
    with pytest.raises(KeyError):
        service.stop("unknown")


@pytest.mark.unit
def test_concurrent_start_raises_when_busy(
    service: RunnerService, existing_yaml: Path, release_event: threading.Event
) -> None:
    service.start(config_path=str(existing_yaml), mode="live", aulas=10, faults=[])
    try:
        with pytest.raises(RuntimeError, match="busy"):
            service.start(config_path=str(existing_yaml), mode="live", aulas=10, faults=[])
    finally:
        release_event.set()


@pytest.mark.unit
def test_status_idle_when_no_jobs(service: RunnerService) -> None:
    assert service.status()["phase"] == "idle"


@pytest.mark.unit
def test_stop_releases_active_slot(
    service: RunnerService, existing_yaml: Path, release_event: threading.Event
) -> None:
    job_id = service.start(config_path=str(existing_yaml), mode="live", aulas=10, faults=[])
    service.stop(job_id)
    release_event.set()
    new_job = service.start(config_path=str(existing_yaml), mode="backfill", aulas=5, faults=[])
    assert new_job != job_id


@pytest.mark.unit
def test_start_with_missing_config_marks_error(
    service: RunnerService, release_event: threading.Event
) -> None:
    release_event.set()
    job_id = service.start(
        config_path="/definitely/does/not/exist.yaml",
        mode="backfill",
        aulas=1,
        faults=[],
    )
    # Wait briefly for the daemon thread to surface the FileNotFoundError.
    for _ in range(50):
        st = service.status(job_id)
        if st["phase"] == "error":
            break
        threading.Event().wait(0.02)
    assert service.status(job_id)["phase"] == "error"
    assert "config not found" in (service.status(job_id)["error"] or "")


@pytest.mark.unit
def test_factory_with_3_tuple_invokes_fault_hook(
    existing_yaml: Path, release_event: threading.Event
) -> None:
    """T-PV-30: factory que devuelve (runner, sink, hook) — hook se invoca y suma puntos."""
    hook_calls: list[int] = []

    def _post_hook() -> int:
        hook_calls.append(1)
        return 42  # extra fault datapoints

    def _factory_3tuple(_path: Path):
        return _FakeRunner(release_event, points=100), object(), _post_hook

    s = RunnerService(runner_factory=_factory_3tuple)
    release_event.set()
    job_id = s.start(
        config_path=str(existing_yaml), mode="backfill", aulas=1, faults=["sensor_drift"]
    )
    for _ in range(50):
        st = s.status(job_id)
        if st["phase"] in {"completed", "error"}:
            break
        threading.Event().wait(0.02)
    st = s.status(job_id)
    assert st["phase"] == "completed"
    # 100 from runner.run() + 42 from hook
    assert st["points_emitted"] == 142
    assert hook_calls == [1]


@pytest.mark.unit
def test_factory_with_3_tuple_handles_hook_exception(
    existing_yaml: Path, release_event: threading.Event
) -> None:
    """Hook que falla NO debe romper el job; debe loggear y continuar."""

    def _failing_hook() -> int:
        raise RuntimeError("simulated hook failure")

    def _factory_3tuple(_path: Path):
        return _FakeRunner(release_event, points=50), object(), _failing_hook

    s = RunnerService(runner_factory=_factory_3tuple)
    release_event.set()
    job_id = s.start(config_path=str(existing_yaml), mode="backfill", aulas=1, faults=[])
    for _ in range(50):
        st = s.status(job_id)
        if st["phase"] in {"completed", "error"}:
            break
        threading.Event().wait(0.02)
    st = s.status(job_id)
    assert st["phase"] == "completed"
    assert st["points_emitted"] == 50  # only runner.run() points
