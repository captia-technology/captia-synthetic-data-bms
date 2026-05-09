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
from collections.abc import Callable, Iterator
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
    # Path resolution robusta: prueba sibling, walk-up desde config, walk-up
    # desde módulo (cubre tests con configs en /tmp).
    faults_yaml = _resolve_domain_config_path(config_path, config.domain.id, "faults.yaml")
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

    # T-PV-21 (cierra L-PV-01 parcialmente): envuelve cada sink con
    # AliasSinkAdapter cuando BMS_PRODUCTION_ALIAS_ENABLED=true (default true).
    # Esto renombra DataPoints vendor → producción ANTES de emit a MQTT/file/Influx.
    sinks = _maybe_wrap_with_alias(sinks, config_path, config.domain.id)

    sink = sinks[0] if len(sinks) == 1 else CompositeSink(sinks)

    # T-PV-08 + T-PV-30: si faults activos, envuelve sink con _LateCloseSink
    # para que sobreviva al close() interno del runner y permita al fault_hook
    # emitir DataPoints adicionales después de runner.run().
    from ..config import get_settings
    if get_settings().faults_enabled and faults_config:
        sink = _LateCloseSink(sink)

    with _suppress_signal_setup():
        runner = ScenarioRunner(config, domain, sink)

    fault_hook = _build_fault_emitter_hook(sink, config, domain, faults_config, config_path)
    if fault_hook is not None:
        return runner, sink, fault_hook
    return runner, sink


class _LateCloseSink:
    """Sink wrapper que difiere ``close()`` hasta ``release_close()``.

    Necesario para T-PV-08/T-PV-30: el vendor ScenarioRunner.run() cierra el
    sink al terminar, lo que rompe el fault_hook posterior. Este wrapper:
      - Delega open/emit/emit_batch/flush al sink real.
      - Intercepta close(): solo flushea (no cierra).
      - Expone release_close() para cerrar de verdad cuando _run_job termina.
    """

    def __init__(self, real_sink: Any):
        self.real_sink = real_sink
        self._released = False

    @property
    def name(self) -> str:
        return getattr(self.real_sink, "name", "late_close")

    def open(self) -> None:
        if hasattr(self.real_sink, "open"):
            self.real_sink.open()

    def emit(self, point: Any) -> Any:
        return self.real_sink.emit(point)

    def emit_batch(self, points: Any) -> int:
        if hasattr(self.real_sink, "emit_batch"):
            return self.real_sink.emit_batch(points)
        n = 0
        for p in points:
            self.real_sink.emit(p)
            n += 1
        return n

    def flush(self) -> None:
        if hasattr(self.real_sink, "flush"):
            self.real_sink.flush()

    def close(self) -> None:
        # Diferir close real — flush sí.
        if hasattr(self.real_sink, "flush"):
            self.real_sink.flush()

    def release_close(self) -> None:
        """Cierra el sink real. Llamar tras invocar el fault_hook."""
        if self._released:
            return
        self._released = True
        if hasattr(self.real_sink, "close"):
            self.real_sink.close()

    # Forward AliasSink-specific properties for tests.
    @property
    def renamed_count(self) -> int:
        return getattr(self.real_sink, "renamed_count", 0)

    @property
    def passthrough_count(self) -> int:
        return getattr(self.real_sink, "passthrough_count", 0)

    @property
    def aliases(self) -> dict:
        return getattr(self.real_sink, "aliases", {})


def _resolve_domain_config_path(config_path: Path, domain_id: str, filename: str) -> Path:
    """Resolve path to a domain-config file (variables.yaml, faults.yaml, ...).

    Tries multiple strategies, in order:
      1. Sibling layout: config_path is config/projects/<scenario>.yaml →
         config_path.parent.parent / "domains" / domain_id / filename
      2. Walk up from config_path looking for `config/domains/<domain_id>/<filename>`.
      3. Walk up from this module file looking for `config/domains/<domain_id>/<filename>`
         (works when config_path is outside the repo, e.g. in /tmp during tests).

    Returns the first existing path, or the strategy-1 path (which won't exist)
    so the caller's `.exists()` check fails informatively.
    """
    candidate = config_path.parent.parent / "domains" / domain_id / filename
    if candidate.exists():
        return candidate

    # Strategy 2: walk up from config_path.
    current = config_path.resolve().parent
    for _ in range(8):
        c = current / "config" / "domains" / domain_id / filename
        if c.exists():
            return c
        if current.parent == current:
            break
        current = current.parent

    # Strategy 3: walk up from this module file.
    current = Path(__file__).resolve().parent
    for _ in range(8):
        c = current / "config" / "domains" / domain_id / filename
        if c.exists():
            return c
        if current.parent == current:
            break
        current = current.parent

    return candidate  # original (non-existing) for informative error


def _maybe_wrap_with_alias(sinks: list, config_path: Path, domain_id: str) -> list:
    """Wrap each sink with AliasSinkAdapter if production_alias_enabled.

    Lazy import to keep unit tests light. Reads alias map from
    ``config/domains/<domain_id>/variables.yaml`` (production_name field).
    Returns the list unchanged if alias is disabled or if the variables.yaml
    has no production_name overrides.
    """
    from ..config import get_settings

    settings = get_settings()
    if not settings.production_alias_enabled:
        return sinks

    from bms_signal_alias import AliasSinkAdapter, build_alias_map_from_yaml

    variables_yaml = _resolve_domain_config_path(config_path, domain_id, "variables.yaml")
    aliases = build_alias_map_from_yaml(variables_yaml)
    if not aliases:
        LOG.info(
            "production_alias enabled but no aliases found at %s — skipping wrap",
            variables_yaml,
        )
        return sinks

    LOG.info(
        "wrapping %d sink(s) with AliasSinkAdapter (%d aliases) using %s",
        len(sinks),
        len(aliases),
        variables_yaml,
    )
    return [AliasSinkAdapter(s, aliases) for s in sinks]


def _build_fault_emitter_hook(
    sink: Any,
    config: Any,
    domain: Any,
    faults_config: dict,
    config_path: Path,
) -> Callable[[], int] | None:
    """Build a post-run hook that emits FaultEvent → DataPoint to the sink.

    Returns a 0-arg callable that, when invoked, generates fault events for
    every asset_id in the inventory using the FaultInjector and emits them
    via FaultEventEmitter. Returns ``None`` if faults are disabled or
    faults_config is empty.

    Closes L-PV-02: con esto, los DataPoints con ``variable=fault.<tipo>``
    aterrizan en MQTT/file, son detectados por Telegraf clone+dedup
    (tagpass ``fault.*``) y enrutados a state_events bucket — habilitando
    Caso C real con etiquetas verdaderas.
    """
    from ..config import get_settings

    settings = get_settings()
    if not settings.faults_enabled or not faults_config:
        return None

    # Lazy imports.
    from collections.abc import Callable  # noqa: F401 — used in return type

    import numpy as np
    import pandas as pd
    import yaml as _yaml

    from bms_calibration import FaultEventEmitter, FaultInjector

    # Build inventory from domain plug-in to get asset_ids list.
    project_cfg = {
        "site_id": config.project.site_id,
        "namespace": config.project.namespace,
    }
    domain_yaml_path = _resolve_domain_config_path(config_path, config.domain.id, "domain.yaml")
    domain_cfg: dict = {}
    if domain_yaml_path.exists():
        with domain_yaml_path.open(encoding="utf-8") as fh:
            domain_cfg = _yaml.safe_load(fh) or {}

    inventory = domain.build_inventory(project_cfg, domain_cfg)
    asset_ids = inventory.list_asset_ids()

    # Build pandas time index from scenario simulation start/end/freq.
    timestamps = (
        pd.date_range(
            start=config.simulation.start,
            end=config.simulation.end,
            freq=config.simulation.freq,
            inclusive="left",
        )
        .to_pydatetime()
        .tolist()
    )

    def hook() -> int:
        emitter = FaultEventEmitter(
            sink,
            domain_id=config.domain.id,
            site_id=config.project.site_id,
        )
        seed = config.simulation.seed
        total = 0
        for idx, asset_id in enumerate(asset_ids):
            # Sub-RNG per asset for reproducibility (mirror del pattern del vendor).
            rng = np.random.default_rng(seed + idx)
            injector = FaultInjector(rng=rng, config=faults_config, seed=seed + idx)
            events = list(injector.inject(timestamps, asset_id))
            total += emitter.emit_events(events)
        LOG.info(
            "fault_emitter hook: emitted %d datapoints across %d assets",
            total,
            len(asset_ids),
        )
        return total

    return hook


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
            # Factory returns (runner, sink) or (runner, sink, fault_hook).
            factory_result = self._runner_factory(config_path)
            if len(factory_result) == 3:
                runner, _sink, fault_hook = factory_result
            else:
                runner, _sink = factory_result
                fault_hook = None
            results = runner.run()
            points = sum(getattr(r, "points_emitted", 0) for r in results)
            # T-PV-30: post-run hook emits FaultEvents to the sink (Caso C real).
            # El sink está envuelto con _LateCloseSink, así que sigue abierto
            # tras runner.run(). Cerramos explícitamente tras el hook.
            if fault_hook is not None:
                try:
                    points += fault_hook() or 0
                except Exception as exc:  # noqa: BLE001
                    LOG.warning("Fault emitter hook failed: %s", exc)
                finally:
                    if hasattr(_sink, "release_close"):
                        _sink.release_close()
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
