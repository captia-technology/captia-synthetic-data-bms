"""Runner service: wraps `synthetic_generator.core.runner.ScenarioRunner`.

Each call to :meth:`RunnerService.start` validates the requested scenario YAML,
allocates a job id and (if the YAML exists) spawns a daemon thread that loads
the config, instantiates the BMS domain plus the configured sinks and runs the
scenario.

Only one active job at a time. Subsequent ``start`` calls raise
``RuntimeError("Runner busy")`` until the active job finishes or is stopped.
"""

from __future__ import annotations

import logging
import signal
import threading
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

LOG = logging.getLogger(__name__)


@dataclass
class _Job:
    job_id: str
    config_path: str
    mode: str
    aulas: int
    faults: list[str] = field(default_factory=list)
    phase: str = "pending"
    started_at: datetime | None = None
    finished_at: datetime | None = None
    points_emitted: int = 0
    error: str | None = None


@contextmanager
def _suppress_signal_setup() -> Iterator[None]:
    """Disable :func:`signal.signal` while the vendor runner is constructed.

    The vendored ``ScenarioRunner.__init__`` registers SIGINT/SIGTERM handlers
    via ``signal.signal``, which only works on the main Python thread. When we
    spawn the runner from a worker thread we patch ``signal.signal`` to a
    no-op for that constructor call.
    """
    original = signal.signal
    signal.signal = lambda *args, **kwargs: None  # type: ignore[assignment]
    try:
        yield
    finally:
        signal.signal = original


def _build_runner(config_path: Path) -> tuple[Any, Any]:
    """Load a scenario config and build (runner, sink_list) ready to run.

    Imported lazily so unit tests that don't touch the vendor stay light.
    """
    from synthetic_generator.core.config import (  # type: ignore[import-not-found]
        SinkType,
        load_scenario_config,
    )
    from synthetic_generator.core.runner import ScenarioRunner  # type: ignore[import-not-found]
    from synthetic_generator.domains.registry import (  # type: ignore[import-not-found]
        auto_discover_domains,
        get_domain,
    )
    from synthetic_generator.sinks.composite import CompositeSink  # type: ignore[import-not-found]
    from synthetic_generator.sinks.file import (  # type: ignore[import-not-found]
        FileSinkAdapter,
        FileSinkConfig,
    )
    from synthetic_generator.sinks.mqtt import (  # type: ignore[import-not-found]
        MQTTSinkAdapter,
        MQTTSinkConfig,
    )
    from synthetic_generator.sinks.stdout import StdoutSinkAdapter  # type: ignore[import-not-found]

    from .calibration_loader import (
        load_faults_config,
        load_physics_overrides,
    )

    auto_discover_domains()

    config = load_scenario_config(config_path)
    domain = get_domain(config.domain.id)
    if domain is None:
        raise ValueError(f"Unknown domain: {config.domain.id}")

    # T-PV-07 (cierra L-PV-04): wire calibration_loader.
    # Carga simbólica de faults_config y physics_overrides para que estén
    # disponibles cuando se implemente FaultInjector wiring (T-PV-08).
    # Por ahora se loggean para verificar cableado; no afectan al runner aún.
    # Path: config_path es config/projects/<scenario>.yaml → faults.yaml está en
    # config/domains/<domain_id>/faults.yaml (sibling directory).
    faults_yaml = config_path.parent.parent / "domains" / config.domain.id / "faults.yaml"
    faults_config = load_faults_config(faults_yaml)
    physics_overrides = load_physics_overrides()
    LOG.info(
        "calibration_loader wired: faults_yaml=%s exists=%s "
        "faults_config=%d types physics_overrides=%d active",
        faults_yaml,
        faults_yaml.exists(),
        len(faults_config),
        len(physics_overrides),
    )

    sinks: list = []
    for sink_cfg in config.sinks:
        if sink_cfg.type == SinkType.MQTT:
            sinks.append(MQTTSinkAdapter(MQTTSinkConfig(**sink_cfg.config)))
        elif sink_cfg.type == SinkType.FILE:
            sinks.append(FileSinkAdapter(FileSinkConfig(**sink_cfg.config)))
        elif sink_cfg.type == SinkType.STDOUT:
            sinks.append(StdoutSinkAdapter())
    if not sinks:
        sinks.append(StdoutSinkAdapter())
    sink = sinks[0] if len(sinks) == 1 else CompositeSink(sinks)

    with _suppress_signal_setup():
        runner = ScenarioRunner(config, domain, sink)
    return runner, sink


RunnerFactory = Any  # Callable[[Path], tuple[ScenarioRunner, sink]]


class RunnerService:
    """In-memory job tracker that drives the vendored scenario runner.

    A custom ``runner_factory`` callable can be injected (mainly for tests)
    to bypass the heavy vendor build path. The factory must accept a
    :class:`Path` to a scenario YAML and return a ``(runner, sink)`` pair
    where ``runner`` exposes a ``.run()`` method returning an iterable of
    results with a ``points_emitted`` attribute.
    """

    def __init__(self, runner_factory: RunnerFactory | None = None) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, _Job] = {}
        self._active_job_id: str | None = None
        self._stop_flags: dict[str, threading.Event] = {}
        self._runner_factory = runner_factory or _build_runner
        self._run_threads = True

    def set_runner_factory(self, factory: RunnerFactory) -> None:
        """Inject a runner factory at runtime (used by integration tests)."""
        self._runner_factory = factory

    def disable_threads(self) -> None:
        """Run jobs synchronously instead of in a daemon thread (tests only)."""
        self._run_threads = False

    def start(
        self,
        config_path: str,
        mode: str,
        aulas: int,
        faults: list[str],
    ) -> str:
        with self._lock:
            if self._active_job_id is not None:
                raise RuntimeError("Runner busy with active job")
            job_id = uuid.uuid4().hex[:12]
            job = _Job(
                job_id=job_id,
                config_path=config_path,
                mode=mode,
                aulas=aulas,
                faults=list(faults),
                phase="pending",
                started_at=datetime.now(tz=UTC),
            )
            self._jobs[job_id] = job
            self._active_job_id = job_id
            self._stop_flags[job_id] = threading.Event()

        cfg_path = Path(config_path)
        if self._run_threads:
            thread = threading.Thread(
                target=self._run_job,
                args=(job_id, cfg_path),
                daemon=True,
                name=f"bms-runner-{job_id}",
            )
            thread.start()
        else:
            self._run_job(job_id, cfg_path)
        return job_id

    def _run_job(self, job_id: str, config_path: Path) -> None:
        with self._lock:
            self._jobs[job_id].phase = "running"
        try:
            if not config_path.is_file():
                raise FileNotFoundError(f"config not found: {config_path}")
            runner, _sink = self._runner_factory(config_path)
            results = runner.run()
            points = sum(getattr(r, "points_emitted", 0) for r in results)
            with self._lock:
                self._jobs[job_id].phase = "completed"
                self._jobs[job_id].points_emitted = points
                self._jobs[job_id].finished_at = datetime.now(tz=UTC)
        except Exception as exc:  # noqa: BLE001 — surface to API
            LOG.exception("Runner job %s failed", job_id)
            self._fail(job_id, str(exc))
        finally:
            with self._lock:
                if self._active_job_id == job_id:
                    self._active_job_id = None

    def _fail(self, job_id: str, reason: str) -> None:
        with self._lock:
            self._jobs[job_id].phase = "error"
            self._jobs[job_id].error = reason
            self._jobs[job_id].finished_at = datetime.now(tz=UTC)
            if self._active_job_id == job_id:
                self._active_job_id = None

    def stop(self, job_id: str) -> None:
        with self._lock:
            if job_id not in self._jobs:
                raise KeyError(job_id)
            self._jobs[job_id].phase = "stopped"
            self._jobs[job_id].finished_at = datetime.now(tz=UTC)
            if job_id in self._stop_flags:
                self._stop_flags[job_id].set()
            if self._active_job_id == job_id:
                self._active_job_id = None

    def status(self, job_id: str | None = None) -> dict:
        with self._lock:
            if job_id is None:
                job_id = self._active_job_id
            if job_id is None or job_id not in self._jobs:
                return {"phase": "idle"}
            j = self._jobs[job_id]
            return {
                "job_id": j.job_id,
                "phase": j.phase,
                "mode": j.mode,
                "aulas": j.aulas,
                "faults": list(j.faults),
                "started_at": j.started_at.isoformat() if j.started_at else None,
                "finished_at": j.finished_at.isoformat() if j.finished_at else None,
                "points_emitted": j.points_emitted,
                "error": j.error,
            }

    def reset(self) -> None:
        """Test helper: drop all job state."""
        with self._lock:
            self._jobs.clear()
            self._active_job_id = None
            self._stop_flags.clear()
