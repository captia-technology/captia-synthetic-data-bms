"""Composite sink adapter — fan-out to multiple sinks.

Ref: docs/specs/sink-adapters.md Section 5
"""
from __future__ import annotations

import logging
from ..core.models import DataPoint

LOG = logging.getLogger(__name__)


class CompositeSink:
    """Fan-out to multiple sink adapters."""

    def __init__(self, sinks: list):
        self._sinks = sinks

    @property
    def name(self) -> str:
        names = [s.name for s in self._sinks]
        return f"composite[{','.join(names)}]"

    def open(self) -> None:
        for s in self._sinks:
            s.open()

    def emit(self, point: DataPoint) -> None:
        for s in self._sinks:
            try:
                s.emit(point)
            except Exception as e:
                LOG.error("Sink %s emit error: %s", s.name, e)

    def emit_batch(self, points: list[DataPoint]) -> int:
        count = 0
        for s in self._sinks:
            try:
                count = max(count, s.emit_batch(points))
            except Exception as e:
                LOG.error("Sink %s emit_batch error: %s", s.name, e)
        return count

    def flush(self) -> None:
        for s in self._sinks:
            s.flush()

    def close(self) -> None:
        for s in self._sinks:
            s.close()
