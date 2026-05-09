"""Null sink adapter — discards all points (for benchmarking)."""
from __future__ import annotations

from ..core.models import DataPoint


class NullSink:
    """No-op sink for benchmarking."""

    def __init__(self):
        self._count = 0

    @property
    def name(self) -> str:
        return "null"

    def open(self) -> None:
        pass

    def emit(self, point: DataPoint) -> None:
        self._count += 1

    def emit_batch(self, points: list[DataPoint]) -> int:
        self._count += len(points)
        return len(points)

    def flush(self) -> None:
        pass

    def close(self) -> None:
        pass

    @property
    def emitted_count(self) -> int:
        return self._count
