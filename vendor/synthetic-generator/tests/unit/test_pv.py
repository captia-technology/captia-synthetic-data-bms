"""Unit tests for PV naming and MQTT topic construction."""
import pytest

from synthetic_generator.core.pv import (
    build_captia_mqtt_topic,
    build_captia_subscribe_pattern,
    build_pvn,
    build_pvp,
    parse_pvn,
    parse_pvp,
)


class TestBuildPVN:
    def test_basic(self):
        assert build_pvn("AULA01", "temperature") == "AULA01__temperature"

    def test_forces_uppercase_asset(self):
        assert build_pvn("aula01", "temperature") == "AULA01__temperature"

    def test_forces_lowercase_variable(self):
        assert build_pvn("AULA01", "Temperature") == "AULA01__temperature"

    def test_double_underscore_separator(self):
        pvn = build_pvn("A", "b")
        assert "__" in pvn
        assert pvn.count("__") == 1


class TestBuildPVP:
    def test_basic(self):
        result = build_pvp("captia", "synthetic", "v0.1", "school1", "AULA01", "temperature")
        assert result == "captia/synthetic/v0.1/school1/AULA01/temperature"

    def test_six_segments(self):
        result = build_pvp("ns", "m", "v1", "s", "A", "v")
        assert result.count("/") == 5


class TestCaptiaMQTTTopic:
    def test_basic(self):
        topic = build_captia_mqtt_topic(
            env="dev", tenant="bms", site="school1", device="AULA01", name="temperature"
        )
        assert topic == "captia/dev/bms/school1/AULA01/telemetry/temperature"

    def test_with_version(self):
        topic = build_captia_mqtt_topic(
            env="dev", tenant="bms", site="s1", device="A01",
            name="temp", version="v1",
        )
        assert topic == "captia/v1/dev/bms/s1/A01/telemetry/temp"

    def test_seven_segments_without_version(self):
        topic = build_captia_mqtt_topic(
            env="dev", tenant="t", site="s", device="d", name="n"
        )
        assert topic.count("/") == 6

    def test_custom_stream(self):
        topic = build_captia_mqtt_topic(
            env="dev", tenant="t", site="s", device="d", stream="cmd", name="setpoint"
        )
        assert "/cmd/" in topic


class TestCaptiaSubscribePattern:
    def test_default_wildcards(self):
        pattern = build_captia_subscribe_pattern()
        assert pattern == "captia/+/+/+/+/+/#"

    def test_specific_tenant(self):
        pattern = build_captia_subscribe_pattern(tenant="acme")
        assert "/acme/" in pattern

    def test_telemetry_only(self):
        pattern = build_captia_subscribe_pattern(stream="telemetry")
        assert "/telemetry/" in pattern


class TestParsePVN:
    def test_basic(self):
        asset_id, var = parse_pvn("AULA01__temperature")
        assert asset_id == "AULA01"
        assert var == "temperature"

    def test_forces_case(self):
        asset_id, var = parse_pvn("aula01__Temperature")
        assert asset_id == "AULA01"
        assert var == "temperature"

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="Invalid PVN"):
            parse_pvn("no_double_underscore")


class TestParsePVP:
    def test_basic(self):
        result = parse_pvp("captia/synthetic/v0.1/school1/AULA01/temperature")
        assert result["namespace"] == "captia"
        assert result["modo"] == "synthetic"
        assert result["schema_version"] == "v0.1"
        assert result["site_id"] == "school1"
        assert result["asset_id"] == "AULA01"
        assert result["variable"] == "temperature"

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="Invalid PVP"):
            parse_pvp("too/few/parts")

    def test_roundtrip(self):
        original = build_pvp("ns", "mode", "v1", "site", "ASSET", "var")
        parsed = parse_pvp(original)
        assert parsed["namespace"] == "ns"
        assert parsed["asset_id"] == "ASSET"
        assert parsed["variable"] == "var"
