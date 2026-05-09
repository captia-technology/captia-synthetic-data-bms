"""Runner service: wrapper sobre vendor.synthetic_generator.core.runner.

En v1 mantiene un único job activo; los siguientes lanzamientos rechazan
con `RuntimeError("Runner busy")`. Estado se persiste en memoria (no DB).
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class _Job:
    job_id: str
    config_path: str
    mode: str
    aulas: int
    faults: list[str] = field(default_factory=list)
    phase: str = "pending"
    started_at: datetime | None = None
    points_emitted: int = 0
    error: str | None = None


class RunnerService:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, _Job] = {}
        self._active_job_id: str | None = None

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
            self._jobs[job_id] = _Job(
                job_id=job_id,
                config_path=config_path,
                mode=mode,
                aulas=aulas,
                faults=list(faults),
                phase="pending",
                started_at=datetime.now(tz=timezone.utc),
            )
            self._active_job_id = job_id
        # En esta versión esqueleto NO se ejecuta vendor.runner.
        # Será integrado en una iteración posterior cuando se valide el wiring uv.
        return job_id

    def stop(self, job_id: str) -> None:
        with self._lock:
            if job_id not in self._jobs:
                raise KeyError(job_id)
            self._jobs[job_id].phase = "stopped"
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
                "points_emitted": j.points_emitted,
                "error": j.error,
            }

    def reset(self) -> None:
        """Solo para tests."""
        with self._lock:
            self._jobs.clear()
            self._active_job_id = None
