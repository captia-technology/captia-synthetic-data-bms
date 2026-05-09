"""Unit tests for ContractValidator."""
from datetime import datetime, timezone

import pytest

from synthetic_generator.core.models import (
    Asset,
    DataPoint,
    DataType,
    Inventory,
    PointType,
    Quality,
    VariableDef,
)
from synthetic_generator.core.validator import ContractValidator


def _make_point(**overrides) -> DataPoint:
    defaults = {
        "timestamp": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "domain_id": "test",
        "site_id": "s",
        "asset_id": "ASSET01",
        "variable": "temp",
        "value": 22.0,
        "unit": "°C",
        "data_type": DataType.FLOAT,
        "point_type": PointType.SENSOR,
    }
    defaults.update(overrides)
    return DataPoint(**defaults)


class TestContractValidator:
    def test_valid_point(self):
        v = ContractValidator()
        result = v.validate(_make_point())
        assert result.valid

    def test_none_timestamp(self):
        v = ContractValidator()
        result = v.validate(_make_point(timestamp=None))
        assert not result.valid
        assert any("timestamp" in e for e in result.errors)

    def test_asset_not_uppercase(self):
        v = ContractValidator()
        # DataPoint.__post_init__ already uppercases, so test raw
        p = _make_point()
        # Manually set lowercase to test validator
        p.asset_id = "lowercase"
        result = v.validate(p)
        assert not result.valid
        assert any("uppercase" in e for e in result.errors)

    def test_variable_not_lowercase(self):
        v = ContractValidator()
        p = _make_point()
        p.variable = "UPPER"
        result = v.validate(p)
        assert not result.valid
        assert any("lowercase" in e for e in result.errors)

    def test_missing_quality_skips_range(self):
        v = ContractValidator()
        p = _make_point(quality=Quality.MISSING)
        result = v.validate(p)
        assert result.valid

    def test_range_check_passes(self):
        var = VariableDef(name="temp", expected_range_hard=(0.0, 50.0))
        asset = Asset(asset_id="ASSET01", asset_type="t", variables=(var,))
        inv = Inventory(domain_id="test", assets=[asset])
        v = ContractValidator(inventory=inv)
        result = v.validate(_make_point(value=25.0))
        assert result.valid

    def test_range_check_fails(self):
        var = VariableDef(name="temp", expected_range_hard=(0.0, 50.0))
        asset = Asset(asset_id="ASSET01", asset_type="t", variables=(var,))
        inv = Inventory(domain_id="test", assets=[asset])
        v = ContractValidator(inventory=inv)
        result = v.validate(_make_point(value=100.0))
        assert not result.valid

    def test_error_count(self):
        v = ContractValidator()
        p = _make_point()
        p.asset_id = "low"
        p.variable = "UP"
        v.validate(p)
        assert v.error_count >= 2
        assert v.validated_count == 1

    def test_validate_batch(self):
        v = ContractValidator()
        points = [_make_point(), _make_point()]
        results = v.validate_batch(points)
        assert len(results) == 2
        assert all(r.valid for r in results)
