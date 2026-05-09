"""File sink adapter — writes DataPoints to CSV or JSONL.

Ref: docs/specs/sink-adapters.md Section 3
"""
from __future__ import annotations

import csv
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, TextIO

from ..core.models import DataPoint
from ..core.pv import build_pvn

LOG = logging.getLogger(__name__)


@dataclass
class FileSinkConfig:
    path: str = "outputs/dataset.csv"
    format: str = "csv_long"  # csv_long | csv_wide | jsonl


CSV_COLUMNS = [
    "timestamp", "domain_id", "site_id", "asset_id", "variable",
    "value", "unit", "data_type", "point_type", "quality", "origin", "pvn",
]


class FileSinkAdapter:
    """File-based sink for CSV and JSONL output."""

    def __init__(self, config: FileSinkConfig):
        self._config = config
        self._file: Optional[TextIO] = None
        self._writer = None
        self._points: list[DataPoint] = []
        self._count = 0

    @property
    def name(self) -> str:
        return "file"

    def open(self) -> None:
        path = Path(self._config.path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if self._config.format == "jsonl":
            self._file = open(path, "w", encoding="utf-8")
        elif self._config.format in ("csv_long", "csv_wide"):
            self._file = open(path, "w", encoding="utf-8", newline="")
            if self._config.format == "csv_long":
                self._writer = csv.DictWriter(self._file, fieldnames=CSV_COLUMNS)
                self._writer.writeheader()
        else:
            self._file = open(path, "w", encoding="utf-8", newline="")
            self._writer = csv.DictWriter(self._file, fieldnames=CSV_COLUMNS)
            self._writer.writeheader()

    def emit(self, point: DataPoint) -> None:
        if self._config.format == "csv_wide":
            self._points.append(point)
        elif self._config.format == "jsonl":
            self._write_jsonl(point)
        else:
            self._write_csv_row(point)
        self._count += 1

    def emit_batch(self, points: list[DataPoint]) -> int:
        for p in points:
            self.emit(p)
        return len(points)

    def flush(self) -> None:
        if self._config.format == "csv_wide" and self._points:
            self._write_wide()
        if self._file:
            self._file.flush()

    def close(self) -> None:
        self.flush()
        if self._file:
            self._file.close()
            self._file = None

    def _write_csv_row(self, point: DataPoint) -> None:
        if self._writer is None:
            return
        ts = point.timestamp.isoformat() if hasattr(point.timestamp, 'isoformat') else str(point.timestamp)
        self._writer.writerow({
            "timestamp": ts,
            "domain_id": point.domain_id,
            "site_id": point.site_id,
            "asset_id": point.asset_id,
            "variable": point.variable,
            "value": self._format_value(point.value),
            "unit": point.unit,
            "data_type": point.data_type.value,
            "point_type": point.point_type.value,
            "quality": point.quality.value,
            "origin": point.origin,
            "pvn": build_pvn(point.asset_id, point.variable),
        })

    def _write_jsonl(self, point: DataPoint) -> None:
        if self._file is None:
            return
        ts = point.timestamp.isoformat() if hasattr(point.timestamp, 'isoformat') else str(point.timestamp)
        record = {
            "timestamp": ts,
            "domain_id": point.domain_id,
            "site_id": point.site_id,
            "asset_id": point.asset_id,
            "variable": point.variable,
            "value": self._format_value(point.value),
            "unit": point.unit,
            "data_type": point.data_type.value,
            "point_type": point.point_type.value,
            "quality": point.quality.value,
            "origin": point.origin,
            "pvn": build_pvn(point.asset_id, point.variable),
        }
        self._file.write(json.dumps(record) + "\n")

    def _write_wide(self) -> None:
        """Write accumulated points in wide (pivot) format."""
        import pandas as pd
        rows = []
        for p in self._points:
            ts = p.timestamp.isoformat() if hasattr(p.timestamp, 'isoformat') else str(p.timestamp)
            rows.append({"timestamp": ts, "asset_id": p.asset_id, "variable": p.variable, "value": self._format_value(p.value)})
        df = pd.DataFrame(rows)
        if not df.empty:
            pivot = df.pivot_table(index=["timestamp", "asset_id"], columns="variable", values="value", aggfunc="first").reset_index()
            pivot.to_csv(self._file, index=False)
        self._points.clear()

    @staticmethod
    def _format_value(value):
        if value is None:
            return ""
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, float):
            return round(value, 4)
        return value

    @property
    def written_count(self) -> int:
        return self._count
