"""Determinism snapshot tests.

Ref: docs/specs/test-strategy.md Section 2.1
Requirement: same seed = identical output
"""
import numpy as np
import pandas as pd
import pytest

from synthetic_generator.core.anomalies import AnomalyConfig, AnomalyEngine
from synthetic_generator.core.models import DataPoint, DataType, Inventory, PointType
from synthetic_generator.core.time_index import build_time_index


SEED = 42


def _points_to_tuples(points: list[DataPoint]) -> list[tuple]:
    """Convert points to comparable tuples (timestamp, asset, variable, value)."""
    return [
        (str(p.timestamp), p.asset_id, p.variable, round(p.value, 6) if isinstance(p.value, float) else p.value)
        for p in points
    ]


@pytest.mark.snapshot
class TestDeterminism:
    """Same seed must produce identical output."""

    def test_time_index_deterministic(self):
        idx1 = build_time_index("2026-01-01", "2026-01-02", "5min", "Europe/Madrid")
        idx2 = build_time_index("2026-01-01", "2026-01-02", "5min", "Europe/Madrid")
        assert (idx1 == idx2).all()

    def test_rng_deterministic(self):
        rng1 = np.random.default_rng(SEED)
        vals1 = [rng1.random() for _ in range(100)]

        rng2 = np.random.default_rng(SEED)
        vals2 = [rng2.random() for _ in range(100)]

        assert vals1 == vals2

    def test_anomaly_engine_deterministic(self):
        """Same seed, same input -> same output from anomaly engine."""
        from datetime import datetime, timezone

        cfg = AnomalyConfig(p_missing=0.1, p_outlier=0.05)
        points = [
            DataPoint(
                timestamp=datetime(2026, 1, 1, i // 60, i % 60, tzinfo=timezone.utc),
                domain_id="test",
                site_id="s",
                asset_id="A",
                variable="v",
                value=float(i),
                unit="u",
                data_type=DataType.FLOAT,
                point_type=PointType.SENSOR,
            )
            for i in range(200)
        ]

        engine1 = AnomalyEngine(cfg, np.random.default_rng(SEED))
        result1 = list(engine1.apply(iter(points)))

        engine2 = AnomalyEngine(cfg, np.random.default_rng(SEED))
        result2 = list(engine2.apply(iter(points)))

        assert len(result1) == len(result2)
        t1 = _points_to_tuples(result1)
        t2 = _points_to_tuples(result2)
        assert t1 == t2

    def test_bms_domain_deterministic(self):
        """BMS domain with same seed produces identical inventory."""
        try:
            from synthetic_generator.domains.bms_classrooms import BMSClassroomsPlugin
        except ImportError:
            pytest.skip("BMS domain not available")

        plugin = BMSClassroomsPlugin()
        project_cfg = {"namespace": "test", "site_id": "test"}
        domain_cfg = {"n_aulas": 3}

        inv1 = plugin.build_inventory(project_cfg, domain_cfg)
        inv2 = plugin.build_inventory(project_cfg, domain_cfg)

        assert len(inv1.assets) == len(inv2.assets)
        for a1, a2 in zip(inv1.assets, inv2.assets):
            assert a1.asset_id == a2.asset_id
            assert len(a1.variables) == len(a2.variables)
