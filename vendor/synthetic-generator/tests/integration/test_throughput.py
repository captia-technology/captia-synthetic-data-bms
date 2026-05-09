"""Throughput benchmark tests.

Ref: docs/specs/test-strategy.md Section 2.3
Acceptance: backfill >= 1000 pts/s
"""
import time
from datetime import datetime, timezone

import numpy as np
import pytest

from synthetic_generator.core.models import DataPoint, DataType, PointType
from synthetic_generator.sinks.null import NullSink


def _generate_points(n: int) -> list[DataPoint]:
    return [
        DataPoint(
            timestamp=datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
            domain_id="bench",
            site_id="s",
            asset_id=f"A{i % 100:03d}",
            variable=f"var_{i % 10}",
            value=float(i),
            unit="u",
            data_type=DataType.FLOAT,
            point_type=PointType.SENSOR,
        )
        for i in range(n)
    ]


@pytest.mark.performance
class TestBackfillThroughput:
    """Test backfill can achieve >= 1000 pts/s."""

    @pytest.mark.timeout(30)
    def test_null_sink_throughput_1000(self):
        """Emit 10k points through NullSink, expect >= 1000 pts/s."""
        n = 10_000
        points = _generate_points(n)
        sink = NullSink()
        sink.open()

        t0 = time.monotonic()
        count = sink.emit_batch(points)
        elapsed = time.monotonic() - t0
        sink.close()

        pts_per_sec = count / max(elapsed, 0.001)
        assert count == n
        assert pts_per_sec >= 1000, f"Throughput too low: {pts_per_sec:.0f} pts/s"

    @pytest.mark.timeout(30)
    def test_file_sink_throughput(self, tmp_path):
        """Emit 5k points through FileSink, measure throughput."""
        from synthetic_generator.sinks.file import FileSinkAdapter, FileSinkConfig

        n = 5_000
        points = _generate_points(n)
        path = str(tmp_path / "bench.csv")
        sink = FileSinkAdapter(FileSinkConfig(path=path, format="csv_long"))
        sink.open()

        t0 = time.monotonic()
        count = sink.emit_batch(points)
        sink.flush()
        elapsed = time.monotonic() - t0
        sink.close()

        pts_per_sec = count / max(elapsed, 0.001)
        assert count == n
        assert pts_per_sec >= 500, f"File sink throughput: {pts_per_sec:.0f} pts/s"

    @pytest.mark.timeout(30)
    def test_validator_throughput(self):
        """Validate 10k points, expect >= 1000 pts/s."""
        from synthetic_generator.core.validator import ContractValidator

        n = 10_000
        points = _generate_points(n)
        validator = ContractValidator()

        t0 = time.monotonic()
        results = validator.validate_batch(points)
        elapsed = time.monotonic() - t0

        pts_per_sec = n / max(elapsed, 0.001)
        assert len(results) == n
        assert pts_per_sec >= 1000, f"Validator throughput: {pts_per_sec:.0f} pts/s"
