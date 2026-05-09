"""Stdout sink adapter — prints DataPoints to stdout.

Ref: docs/specs/sink-adapters.md Section 4
"""
from __future__ import annotations

import json
import sys

from ..core.models import DataPoint


class StdoutSinkAdapter:
    """Prints data points to stdout as JSON (same format as MQTT payload)."""

    def __init__(self, fmt: str = "json"):
        self._fmt = fmt
        self._count = 0

    @property
    def name(self) -> str:
        return "stdout"

    def open(self) -> None:
        pass

    def emit(self, point: DataPoint) -> None:
        if point.value is None:
            return
        if hasattr(point.timestamp, 'timestamp'):
            ts_ns = int(point.timestamp.timestamp() * 1e9)
        else:
            import pandas as pd
            ts_ns = int(pd.Timestamp(point.timestamp).timestamp() * 1e9)

        value = point.value
        if isinstance(value, bool):
            value = 1.0 if value else 0.0
        elif isinstance(value, str):
            # String values are skipped (same as MQTT sink)
            return

        data = {
            "topic": f"captia/dev/default/default/{point.asset_id}/telemetry/{point.variable}",
            "value": value,
            "ts_ns": ts_ns,
        }
        sys.stdout.write(json.dumps(data) + "\n")
        self._count += 1

    def emit_batch(self, points: list[DataPoint]) -> int:
        for p in points:
            self.emit(p)
        return len(points)

    def flush(self) -> None:
        sys.stdout.flush()

    def close(self) -> None:
        pass

    @property
    def emitted_count(self) -> int:
        return self._count
