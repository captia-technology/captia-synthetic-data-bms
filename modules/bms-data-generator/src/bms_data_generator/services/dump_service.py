"""Dump export service: backfill → archivo line-protocol.

En v1 mantiene una cola simple de jobs en memoria con UUID.
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class _DumpJob:
    job_id: str
    months: int
    format: str
    include_faults: bool
    output_path: Path
    status: str = "pending"
    progress: float = 0.0
    size_bytes: int = 0
    sha256: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None


class DumpService:
    def __init__(self, output_dir: Path) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, _DumpJob] = {}
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)

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
                status="in_progress",
                started_at=datetime.now(tz=timezone.utc),
            )
        # Ejecución real del backfill se integra al cablear con vendor.runner.
        return job_id, output_path

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
        """Solo para tests."""
        with self._lock:
            self._jobs.clear()
