"""Unit tests for MQTT sink wire format compliance.

Tests the captia JSON mode:
- Payload: {"value": X, "ts_ns": N}
- Topic: captia/{env}/{tenant}/{site}/{device}/telemetry/{name}

Ref: docs/specs/sink-adapters.md Section 2.2
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from synthetic_generator.core.models import DataPoint, DataType, PointType
from synthetic_generator.sinks.mqtt import MQTTSinkAdapter, MQTTSinkConfig


def _make_point(
    value=22.5,
    variable="temperature",
    asset_id="AULA01",
    domain_id="test_domain",
    site_id="test_site",
) -> DataPoint:
    return DataPoint(
        timestamp=datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        domain_id=domain_id,
        site_id=site_id,
        asset_id=asset_id,
        variable=variable,
        value=value,
        unit="°C",
        data_type=DataType.FLOAT,
        point_type=PointType.SENSOR,
    )


# =========================================================================
# Captia JSON mode tests (the only mode)
# =========================================================================


class TestCaptiaMode:
    """Test captia mode: JSON payload + canonical topic.

    Telegraf Input (captia/#, JSON) produces InfluxDB schema:
      measurement=captia_point, tags: domain_id, site_id, asset_id, variable
    """

    def test_default_config(self):
        """MQTTSinkConfig defaults produce captia namespace."""
        cfg = MQTTSinkConfig()
        assert cfg.captia_prefix == "captia"
        assert cfg.payload_format == "json"

    def test_captia_topic_format(self):
        """Topic: captia/{env}/{tenant}/{site}/{device}/telemetry/{name}."""
        sink = MQTTSinkAdapter(MQTTSinkConfig(captia_env="dev"))
        point = _make_point(domain_id="discrete_mfg", site_id="plant_a", asset_id="M01")
        topic = sink._build_topic(point)
        assert topic == "captia/dev/discrete_mfg/plant_a/M01/telemetry/temperature"

    def test_captia_topic_uses_datapoint_domain(self):
        """domain_id from DataPoint takes priority over config captia_tenant."""
        sink = MQTTSinkAdapter(MQTTSinkConfig(captia_tenant="config_value"))
        point = _make_point(domain_id="from_datapoint")
        topic = sink._build_topic(point)
        assert "/from_datapoint/" in topic

    def test_captia_topic_fallback_to_config(self):
        """When DataPoint.domain_id is empty, fall back to config captia_tenant."""
        sink = MQTTSinkAdapter(MQTTSinkConfig(captia_tenant="fallback_tenant"))
        point = _make_point(domain_id="")
        topic = sink._build_topic(point)
        assert "/fallback_tenant/" in topic

    def test_json_payload_basic_float(self):
        """JSON payload: {"value": 22.5, "ts_ns": <nanoseconds>}."""
        sink = MQTTSinkAdapter(MQTTSinkConfig())
        payload = sink._build_json_payload(_make_point(value=22.5))
        assert payload is not None
        data = json.loads(payload)
        assert data["value"] == 22.5
        assert "ts_ns" in data
        assert isinstance(data["ts_ns"], int)
        assert data["ts_ns"] > 0

    def test_json_payload_boolean_to_float(self):
        """Booleans are converted to 1.0/0.0 (matches captia_point float schema)."""
        sink = MQTTSinkAdapter(MQTTSinkConfig())
        payload_true = sink._build_json_payload(_make_point(value=True))
        payload_false = sink._build_json_payload(_make_point(value=False))
        assert json.loads(payload_true)["value"] == 1.0
        assert json.loads(payload_false)["value"] == 0.0

    def test_json_payload_integer(self):
        """Integer values are preserved."""
        sink = MQTTSinkAdapter(MQTTSinkConfig())
        payload = sink._build_json_payload(_make_point(value=42))
        assert json.loads(payload)["value"] == 42

    def test_json_payload_none_returns_none(self):
        """None values produce no payload."""
        sink = MQTTSinkAdapter(MQTTSinkConfig())
        assert sink._build_json_payload(_make_point(value=None)) is None

    def test_json_payload_string_returns_none(self):
        """String values are dropped (can't store as float in captia_point)."""
        sink = MQTTSinkAdapter(MQTTSinkConfig())
        assert sink._build_json_payload(_make_point(value="PRD_A")) is None

    def test_json_payload_negative(self):
        sink = MQTTSinkAdapter(MQTTSinkConfig())
        data = json.loads(sink._build_json_payload(_make_point(value=-5.3)))
        assert data["value"] == -5.3

    def test_json_payload_zero(self):
        sink = MQTTSinkAdapter(MQTTSinkConfig())
        data = json.loads(sink._build_json_payload(_make_point(value=0)))
        assert data["value"] == 0


# =========================================================================
# Topic structure tests
# =========================================================================


class TestTopicStructure:
    """Verify topic encodes all required tags for Telegraf regex extraction."""

    def test_captia_topic_carries_all_required_tags(self):
        """Captia topic encodes domain_id, site_id, asset_id, variable for regex extraction."""
        point = _make_point(
            domain_id="discrete_manufacturing",
            site_id="plant_faraone",
            asset_id="M01",
            variable="power_kw",
        )
        sink = MQTTSinkAdapter(MQTTSinkConfig(captia_env="dev"))
        topic = sink._build_topic(point)

        # Telegraf regex: captia/{env}/{tenant}/{site}/{asset}/{stream}/{name}
        segments = topic.split("/")
        assert len(segments) == 7
        assert segments[0] == "captia"
        assert segments[1] == "dev"  # captia_env
        assert segments[2] == "discrete_manufacturing"  # -> domain_id
        assert segments[3] == "plant_faraone"  # -> site_id
        assert segments[4] == "M01"  # -> asset_id
        assert segments[5] == "telemetry"  # stream
        assert segments[6] == "power_kw"  # -> variable

    def test_synthetic_is_just_another_tenant(self):
        """domain_id for synthetic data is a normal value, not a special route."""
        point = _make_point(domain_id="discrete_manufacturing", site_id="plant_faraone")
        sink = MQTTSinkAdapter(MQTTSinkConfig(captia_env="dev"))
        topic = sink._build_topic(point)
        # The topic has the same structure as a real device
        assert topic.startswith("captia/dev/discrete_manufacturing/")

    def test_topic_with_version_segment(self):
        """When captia_version is set, it appears after the prefix."""
        sink = MQTTSinkAdapter(MQTTSinkConfig(captia_env="dev", captia_version="v1"))
        point = _make_point(domain_id="dm", site_id="s1", asset_id="A01")
        topic = sink._build_topic(point)
        assert topic.startswith("captia/v1/dev/")
