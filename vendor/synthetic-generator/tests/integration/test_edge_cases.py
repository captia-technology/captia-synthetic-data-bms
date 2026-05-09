"""Edge case integration tests.

Ref: docs/specs/test-strategy.md Section 2.4
"""
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pytest

from synthetic_generator.core.models import (
    Asset,
    DataPoint,
    DataType,
    Inventory,
    PointType,
    VariableDef,
)
from synthetic_generator.core.time_index import build_time_index
from synthetic_generator.core.validator import ContractValidator
from synthetic_generator.sinks.null import NullSink


@pytest.mark.integration
class TestEmptyInventory:
    def test_zero_assets_no_crash(self):
        inv = Inventory(domain_id="empty", assets=[])
        validator = ContractValidator(inventory=inv)
        assert inv.list_asset_ids() == []
        # Validator should handle gracefully
        batch = validator.validate_batch([])
        assert batch == []

    def test_zero_variables(self):
        asset = Asset(asset_id="A", asset_type="t", variables=())
        inv = Inventory(domain_id="test", assets=[asset])
        assert inv.list_variables("A") == []


@pytest.mark.integration
class TestSingleTimestamp:
    def test_one_timestamp(self):
        idx = build_time_index("2026-01-01", "2026-01-01", "5min")
        assert len(idx) == 1

    def test_one_point_through_sink(self):
        sink = NullSink()
        sink.open()
        p = DataPoint(
            timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
            domain_id="t",
            site_id="s",
            asset_id="A",
            variable="v",
            value=1.0,
            unit="u",
            data_type=DataType.FLOAT,
            point_type=PointType.SENSOR,
        )
        sink.emit(p)
        sink.close()
        assert sink.emitted_count == 1


@pytest.mark.integration
class TestNoneValues:
    def test_none_value_in_validator(self):
        validator = ContractValidator()
        p = DataPoint(
            timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
            domain_id="t",
            site_id="s",
            asset_id="A",
            variable="v",
            value=None,
            unit="u",
            data_type=DataType.FLOAT,
            point_type=PointType.SENSOR,
        )
        result = validator.validate(p)
        assert result.valid  # None values should be valid (handled by anomaly engine)

    def test_none_value_in_json_payload(self):
        from synthetic_generator.sinks.mqtt import MQTTSinkAdapter, MQTTSinkConfig
        sink = MQTTSinkAdapter(MQTTSinkConfig())
        p = DataPoint(
            timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
            domain_id="t",
            site_id="s",
            asset_id="A",
            variable="v",
            value=None,
            unit="u",
            data_type=DataType.FLOAT,
            point_type=PointType.SENSOR,
        )
        payload = sink._build_json_payload(p)
        assert payload is None  # None values should produce no payload


@pytest.mark.integration
class TestLargeBatch:
    def test_1000_points_through_null_sink(self):
        sink = NullSink()
        sink.open()
        points = [
            DataPoint(
                timestamp=datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
                domain_id="t",
                site_id="s",
                asset_id=f"A{i:04d}",
                variable="v",
                value=float(i),
                unit="u",
                data_type=DataType.FLOAT,
                point_type=PointType.SENSOR,
            )
            for i in range(1000)
        ]
        count = sink.emit_batch(points)
        sink.close()
        assert count == 1000
        assert sink.emitted_count == 1000

    def test_validator_batch_1000(self):
        validator = ContractValidator()
        points = [
            DataPoint(
                timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
                domain_id="t",
                site_id="s",
                asset_id="A",
                variable="v",
                value=float(i),
                unit="u",
                data_type=DataType.FLOAT,
                point_type=PointType.SENSOR,
            )
            for i in range(1000)
        ]
        results = validator.validate_batch(points)
        assert len(results) == 1000
        assert all(r.valid for r in results)
