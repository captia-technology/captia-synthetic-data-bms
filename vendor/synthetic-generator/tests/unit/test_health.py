"""Tests for the health-check HTTP server.

Tests the HealthServer, GeneratorMetrics and HealthStatus classes.
"""
from __future__ import annotations

import json
import urllib.request

import pytest

from synthetic_generator.health import (
    GeneratorMetrics,
    HealthStatus,
    start_health_server,
    update_status,
)


@pytest.fixture
def health_server():
    """Start health server on an ephemeral port."""
    server = start_health_server(port=0)  # OS picks free port
    port = server.server.server_address[1]
    yield port
    server.stop()


class TestHealthEndpoint:
    def test_health_returns_200(self, health_server):
        port = health_server
        url = f"http://127.0.0.1:{port}/health"
        with urllib.request.urlopen(url) as resp:
            assert resp.status == 200
            body = json.loads(resp.read())
            assert "healthy" in body
            assert "checks" in body
            assert "timestamp" in body

    def test_health_state_updates(self, health_server):
        port = health_server
        update_status("backfill", domain="test")
        url = f"http://127.0.0.1:{port}/health"
        with urllib.request.urlopen(url) as resp:
            body = json.loads(resp.read())
            assert body["healthy"] is True
            assert body["checks"]["config_loaded"] is True
            assert body["domain"] is not None

    def test_404_on_unknown_path(self, health_server):
        port = health_server
        url = f"http://127.0.0.1:{port}/unknown"
        with pytest.raises(urllib.error.HTTPError) as exc_info:
            urllib.request.urlopen(url)
        assert exc_info.value.code == 404

    def test_metrics_endpoint(self, health_server):
        port = health_server
        url = f"http://127.0.0.1:{port}/metrics"
        with urllib.request.urlopen(url) as resp:
            assert resp.status == 200
            content = resp.read().decode()
            assert "captia_generator_messages_published_total" in content
            assert "captia_generator_uptime_seconds" in content

    def test_metrics_json_endpoint(self, health_server):
        port = health_server
        url = f"http://127.0.0.1:{port}/metrics/json"
        with urllib.request.urlopen(url) as resp:
            assert resp.status == 200
            body = json.loads(resp.read())
            assert "messages_published_total" in body
            assert "uptime_seconds" in body


class TestGeneratorMetrics:
    def test_defaults(self):
        m = GeneratorMetrics()
        assert m.messages_published_total == 0
        assert m.publish_errors_total == 0
        assert m.connected_to_mqtt is False

    def test_increment_published(self):
        m = GeneratorMetrics()
        m.increment_published("captia/dev/dm/site/M01/telemetry/power_kw", count=5)
        assert m.messages_published_total == 5
        assert m.messages_by_topic["captia/dev/dm/site/M01/telemetry/power_kw"] == 5
        assert m.last_publish_timestamp is not None

    def test_increment_errors(self):
        m = GeneratorMetrics()
        m.increment_errors(3)
        assert m.publish_errors_total == 3

    def test_to_prometheus(self):
        m = GeneratorMetrics()
        m.increment_published("captia/dev/dm/site/M01/telemetry/temp")
        prom = m.to_prometheus()
        assert "captia_generator_messages_published_total" in prom
        assert "captia_generator_messages_by_topic_total" in prom

    def test_to_dict(self):
        m = GeneratorMetrics()
        d = m.to_dict()
        assert "messages_published_total" in d
        assert "uptime_seconds" in d


class TestHealthStatus:
    def test_defaults(self):
        h = HealthStatus()
        assert h.healthy is True
        assert h.config_loaded is False
        assert h.mqtt_connected is False

    def test_to_dict(self):
        h = HealthStatus(healthy=True, config_loaded=True)
        d = h.to_dict()
        assert d["healthy"] is True
        assert d["checks"]["config_loaded"] is True
