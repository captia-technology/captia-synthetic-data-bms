"""Unit tests for core data models."""
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


class TestVariableDef:
    def test_lowercase_name(self):
        v = VariableDef(name="Temperature")
        assert v.name == "temperature"

    def test_already_lowercase(self):
        v = VariableDef(name="humidity")
        assert v.name == "humidity"

    def test_frozen(self):
        v = VariableDef(name="temp")
        with pytest.raises(AttributeError):
            v.name = "other"

    def test_defaults(self):
        v = VariableDef(name="x")
        assert v.data_type == DataType.FLOAT
        assert v.unit == ""
        assert v.point_type == PointType.SENSOR
        assert v.expected_range_soft is None
        assert v.expected_range_hard is None
        assert v.is_optional is False

    def test_range_soft_hard(self):
        v = VariableDef(
            name="t",
            expected_range_soft=(18.0, 28.0),
            expected_range_hard=(5.0, 45.0),
        )
        assert v.expected_range_soft == (18.0, 28.0)
        assert v.expected_range_hard == (5.0, 45.0)


class TestAsset:
    def test_uppercase_id(self):
        a = Asset(asset_id="aula01", asset_type="classroom")
        assert a.asset_id == "AULA01"

    def test_already_uppercase(self):
        a = Asset(asset_id="AULA01", asset_type="room")
        assert a.asset_id == "AULA01"

    def test_variables_tuple(self, sample_variable_def):
        a = Asset(asset_id="A", asset_type="t", variables=(sample_variable_def,))
        assert len(a.variables) == 1
        assert a.variables[0].name == "temperature"


class TestInventory:
    def test_get_asset(self, sample_inventory):
        asset = sample_inventory.get_asset("AULA01")
        assert asset is not None
        assert asset.asset_id == "AULA01"

    def test_get_asset_case_insensitive(self, sample_inventory):
        asset = sample_inventory.get_asset("aula01")
        assert asset is not None

    def test_get_asset_not_found(self, sample_inventory):
        assert sample_inventory.get_asset("NONEXISTENT") is None

    def test_list_asset_ids(self, sample_inventory):
        ids = sample_inventory.list_asset_ids()
        assert ids == ["AULA01"]

    def test_list_variables(self, sample_inventory):
        vars_ = sample_inventory.list_variables("AULA01")
        assert "temperature" in vars_

    def test_list_variables_unknown_asset(self, sample_inventory):
        assert sample_inventory.list_variables("UNKNOWN") == []

    def test_empty_inventory(self, empty_inventory):
        assert empty_inventory.list_asset_ids() == []
        assert empty_inventory.get_asset("X") is None


class TestDataPoint:
    def test_uppercase_asset_lowercase_variable(self):
        dp = DataPoint(
            timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
            domain_id="test",
            site_id="s",
            asset_id="lower_case",
            variable="UPPER_VAR",
            value=1.0,
            unit="u",
            data_type=DataType.FLOAT,
            point_type=PointType.SENSOR,
        )
        assert dp.asset_id == "LOWER_CASE"
        assert dp.variable == "upper_var"

    def test_quality_default(self, sample_data_point):
        assert sample_data_point.quality == Quality.OK


class TestDataType:
    def test_all_values(self):
        expected = {"float", "integer", "boolean", "string", "enum"}
        assert {dt.value for dt in DataType} == expected


class TestQuality:
    def test_all_values(self):
        expected = {"OK", "MISSING", "OUTLIER", "INTERPOLATED", "SUSPECT"}
        assert {q.value for q in Quality} == expected
