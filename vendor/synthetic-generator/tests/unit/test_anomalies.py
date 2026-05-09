"""Unit tests for anomaly injection engine."""
from datetime import datetime, timezone

import numpy as np
import pytest

from synthetic_generator.core.anomalies import AnomalyConfig, AnomalyEngine
from synthetic_generator.core.models import DataPoint, DataType, PointType, Quality


def _make_point(value=22.5, i=0) -> DataPoint:
    return DataPoint(
        timestamp=datetime(2026, 1, 1, 0, i % 60, tzinfo=timezone.utc),
        domain_id="test",
        site_id="s",
        asset_id="A",
        variable="v",
        value=value,
        unit="u",
        data_type=DataType.FLOAT,
        point_type=PointType.SENSOR,
    )


class TestAnomalyConfig:
    def test_defaults(self):
        cfg = AnomalyConfig()
        assert cfg.p_missing == 0.0
        assert cfg.p_outlier == 0.0
        assert cfg.burst_missing_prob_per_day == 0.0

    def test_custom(self):
        cfg = AnomalyConfig(p_missing=0.05, p_outlier=0.02)
        assert cfg.p_missing == 0.05
        assert cfg.p_outlier == 0.02


class TestAnomalyEngine:
    def test_no_anomalies_passes_through(self):
        cfg = AnomalyConfig()
        engine = AnomalyEngine(cfg, np.random.default_rng(42))
        points = [_make_point(i=i) for i in range(100)]
        result = list(engine.apply(iter(points)))
        assert len(result) == 100

    def test_missing_reduces_count(self):
        cfg = AnomalyConfig(p_missing=0.5)
        engine = AnomalyEngine(cfg, np.random.default_rng(42))
        points = [_make_point(i=i) for i in range(1000)]
        result = list(engine.apply(iter(points)))
        assert len(result) < 1000
        assert len(result) > 100  # Shouldn't remove too many

    def test_outlier_changes_quality(self):
        cfg = AnomalyConfig(p_outlier=1.0)  # All outliers
        engine = AnomalyEngine(cfg, np.random.default_rng(42))
        points = [_make_point(i=i) for i in range(10)]
        result = list(engine.apply(iter(points)))
        assert all(p.quality == Quality.OUTLIER for p in result)

    def test_outlier_changes_value(self):
        cfg = AnomalyConfig(p_outlier=1.0)
        engine = AnomalyEngine(cfg, np.random.default_rng(42))
        p = _make_point(value=22.5)
        result = engine.process(p)
        assert result is not None
        assert result.value != 22.5

    def test_deterministic(self):
        cfg = AnomalyConfig(p_missing=0.1, p_outlier=0.1)
        points = [_make_point(i=i) for i in range(100)]

        engine1 = AnomalyEngine(cfg, np.random.default_rng(42))
        result1 = list(engine1.apply(iter(points)))

        engine2 = AnomalyEngine(cfg, np.random.default_rng(42))
        result2 = list(engine2.apply(iter(points)))

        assert len(result1) == len(result2)

    def test_process_none_for_missing(self):
        cfg = AnomalyConfig(p_missing=1.0)
        engine = AnomalyEngine(cfg, np.random.default_rng(42))
        result = engine.process(_make_point())
        assert result is None

    def test_string_value_outlier(self):
        cfg = AnomalyConfig(p_outlier=1.0)
        engine = AnomalyEngine(cfg, np.random.default_rng(42))
        p = _make_point(value="on")
        result = engine.process(p)
        assert result is not None
        assert result.quality == Quality.OUTLIER
        assert result.value == "on"  # String values unchanged
