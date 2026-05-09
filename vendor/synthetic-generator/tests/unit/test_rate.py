"""Unit tests for RateController."""
from datetime import datetime, timezone

import numpy as np
import pytest

from synthetic_generator.core.clock import FakeClock
from synthetic_generator.core.models import DataPoint, DataType, PointType
from synthetic_generator.core.rate import EmitEvent, RateConfig, RateController


def _make_points(n: int) -> list[DataPoint]:
    return [
        DataPoint(
            timestamp=datetime(2026, 1, 1, 0, i, tzinfo=timezone.utc),
            domain_id="t",
            site_id="s",
            asset_id="A",
            variable="v",
            value=float(i),
            unit="u",
            data_type=DataType.FLOAT,
            point_type=PointType.SENSOR,
        )
        for i in range(n)
    ]


class TestRateController:
    def test_no_perturbations(self):
        rng = np.random.default_rng(42)
        cfg = RateConfig()
        rc = RateController(cfg, rng)
        batch = _make_points(5)
        events = list(rc.pace(batch))
        assert len(events) == 5
        assert all(not e.is_gap for e in events)
        assert all(not e.is_duplicate for e in events)

    def test_gap_injection(self):
        rng = np.random.default_rng(42)
        cfg = RateConfig(gap_probability=0.5, gap_duration_points=(1, 2))
        rc = RateController(cfg, rng)
        batch = _make_points(20)
        events = list(rc.pace(batch))
        gaps = [e for e in events if e.is_gap]
        assert len(gaps) > 0

    def test_duplicate_injection(self):
        rng = np.random.default_rng(42)
        cfg = RateConfig(duplicate_probability=0.5)
        rc = RateController(cfg, rng)
        batch = _make_points(20)
        events = list(rc.pace(batch))
        dups = [e for e in events if e.is_duplicate]
        assert len(dups) > 0
        assert len(events) > 20  # More events due to duplicates

    def test_jitter(self):
        rng = np.random.default_rng(42)
        cfg = RateConfig(jitter_ms=100.0)
        rc = RateController(cfg, rng)
        batch = _make_points(10)
        events = list(rc.pace(batch))
        delays = [e.delay_ms for e in events if not e.is_gap]
        assert any(d > 0 for d in delays)

    def test_wait_for_interval(self):
        clock = FakeClock()
        rng = np.random.default_rng(42)
        cfg = RateConfig(points_per_second=10.0)
        rc = RateController(cfg, rng, clock)
        rc.wait_for_interval(0.05)
        assert len(clock.sleep_calls) == 1
        assert clock.sleep_calls[0] > 0

    def test_wait_for_interval_no_sleep_if_elapsed(self):
        clock = FakeClock()
        rng = np.random.default_rng(42)
        cfg = RateConfig(points_per_second=10.0)
        rc = RateController(cfg, rng, clock)
        rc.wait_for_interval(1.0)  # Already exceeded interval
        assert len(clock.sleep_calls) == 0

    def test_deterministic(self):
        cfg = RateConfig(gap_probability=0.3, duplicate_probability=0.2, jitter_ms=50.0)
        events1 = list(RateController(cfg, np.random.default_rng(42)).pace(_make_points(30)))
        events2 = list(RateController(cfg, np.random.default_rng(42)).pace(_make_points(30)))
        assert len(events1) == len(events2)
        for e1, e2 in zip(events1, events2):
            assert e1.is_gap == e2.is_gap
            assert e1.is_duplicate == e2.is_duplicate
