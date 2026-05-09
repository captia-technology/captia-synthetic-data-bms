"""Dump export service.

Wraps :class:`synthetic_generator.core.runner.ScenarioRunner` to write the
backfill phase of a scenario into a single line-protocol or CSV file under
``output_dir``. Each export is a job with a UUID; jobs run on daemon threads.
"""

from __future__ import annotations

import hashlib
import logging
import threading
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

LOG = logging.getLogger(__name__)


@dataclass
class _DumpJob:
    job_id: str
    months: int
    format: str
    include_faults: bool
    output_path: Path
    config_path: str | None
    status: str = "pending"
    progress: float = 0.0
    size_bytes: int = 0
    sha256: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None


DumpRunnerFactory = Any  # Callable[[_DumpJob], list[Any]]


class DumpService:
    def __init__(
        self,
        output_dir: Path,
        runner_factory: DumpRunnerFactory | None = None,
    ) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, _DumpJob] = {}
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._runner_factory = runner_factory or self._default_runner_factory
        self._run_threads = True

    def set_runner_factory(self, factory: DumpRunnerFactory) -> None:
        self._runner_factory = factory

    def disable_threads(self) -> None:
        self._run_threads = False

    def export(
        self,
        months: int,
        format: str,
        include_faults: bool,
        config_path: str | None = None,
    ) -> tuple[str, Path]:
        if format not in {"line_protocol", "csv_long"}:
            raise ValueError(f"Unsupported format: {format}")
        if not (1 <= months <= 24):
            raise ValueError(f"months out of range: {months}")

        with self._lock:
            job_id = uuid.uuid4().hex[:12]
            ext = "lp" if format == "line_protocol" else "csv"
            output_path = self._output_dir / f"ies_simarro_{months}m_{job_id}.{ext}"
            self._jobs[job_id] = _DumpJob(
                job_id=job_id,
                months=months,
                format=format,
                include_faults=include_faults,
                output_path=output_path,
                config_path=config_path,
                status="in_progress",
                started_at=datetime.now(tz=UTC),
            )

        if self._run_threads:
            thread = threading.Thread(
                target=self._run_job,
                args=(job_id,),
                daemon=True,
                name=f"bms-dump-{job_id}",
            )
            thread.start()
        else:
            self._run_job(job_id)
        return job_id, output_path

    def _run_job(self, job_id: str) -> None:
        with self._lock:
            job = self._jobs[job_id]
        try:
            if job.config_path is None or not Path(job.config_path).is_file():
                raise FileNotFoundError(f"config not found: {job.config_path or '<unset>'}")

            results = self._runner_factory(job)
            points = sum(getattr(r, "points_emitted", 0) for r in results)

            size = job.output_path.stat().st_size if job.output_path.exists() else 0
            digest = self._sha256(job.output_path) if job.output_path.exists() else None

            with self._lock:
                job.status = "done"
                job.progress = 1.0
                job.size_bytes = size
                job.sha256 = digest
                job.finished_at = datetime.now(tz=UTC)
                LOG.info(
                    "dump %s done: %s (%d bytes, %d points)",
                    job.job_id,
                    job.output_path,
                    size,
                    points,
                )
        except Exception as exc:  # noqa: BLE001
            LOG.exception("dump job %s failed", job_id)
            with self._lock:
                job.status = "error"
                job.error = str(exc)
                job.finished_at = datetime.now(tz=UTC)

    def _default_runner_factory(self, job: _DumpJob) -> list[Any]:
        """Build a runner that writes to ``job.output_path`` and execute it."""
        from bms_data_generator.services.runner_service import _suppress_signal_setup
        from synthetic_generator.core.config import (  # type: ignore[import-not-found]
            load_scenario_config,
        )
        from synthetic_generator.core.runner import ScenarioRunner  # type: ignore[import-not-found]
        from synthetic_generator.domains.registry import (  # type: ignore[import-not-found]
            auto_discover_domains,
            get_domain,
        )
        from synthetic_generator.sinks.file import (  # type: ignore[import-not-found]
            FileSinkAdapter,
            FileSinkConfig,
        )

        auto_discover_domains()
        config = load_scenario_config(Path(job.config_path or ""))
        # Force backfill on, live off, regardless of YAML choices.
        config.phases.backfill.enabled = True
        config.phases.live.enabled = False

        domain = get_domain(config.domain.id)
        if domain is None:
            raise ValueError(f"Unknown domain: {config.domain.id}")

        sink = FileSinkAdapter(FileSinkConfig(path=str(job.output_path), format=job.format))

        # T-PV-21: aplica AliasSinkAdapter al dump file también para que el
        # CSV/LP exportado tenga nombres producción (consumible por modelos ML
        # entrenados contra simarro-prod).
        from .runner_service import _maybe_wrap_with_alias

        config_path = Path(job.config_path or "")
        wrapped = _maybe_wrap_with_alias([sink], config_path, config.domain.id)
        sink = wrapped[0]

        with _suppress_signal_setup():
            runner = ScenarioRunner(config, domain, sink)
        return runner.run()

    @staticmethod
    def _sha256(path: Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 16), b""):
                h.update(chunk)
        return h.hexdigest()

    def get(self, job_id: str) -> dict:
        with self._lock:
            j = self._jobs.get(job_id)
            if j is None:
                raise KeyError(job_id)
            return {
                "job_id": j.job_id,
                "status": j.status,
                "progress": round(j.progress, 4),
                "output_path": str(j.output_path),
                "size_bytes": j.size_bytes,
                "sha256": j.sha256,
                "started_at": j.started_at.isoformat() if j.started_at else None,
                "finished_at": j.finished_at.isoformat() if j.finished_at else None,
                "error": j.error,
            }

    def reset(self) -> None:
        """Test helper."""
        with self._lock:
            self._jobs.clear()
