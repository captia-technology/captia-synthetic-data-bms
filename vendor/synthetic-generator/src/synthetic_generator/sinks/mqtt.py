"""MQTT sink adapter — publishes DataPoints to MQTT.

Topic: captia/{env}/{tenant}/{site}/{device}/telemetry/{name}
Payload: JSON {"value": X, "ts_ns": N}

Telegraf parses via captia/# (JSON input) and writes to InfluxDB as:
  measurement=captia_point, tags: domain_id, site_id, asset_id, variable, field: value
"""
from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass
from typing import Optional

import pandas as pd

from ..core.models import DataPoint

LOG = logging.getLogger(__name__)

_SAFE_ID_RE = re.compile(r"^[a-zA-Z0-9_\-\.]{1,128}$")


@dataclass
class MQTTSinkConfig:
    broker_url: str = "tcp://localhost:1883"
    qos: int = 0
    client_id: str = ""
    payload_format: str = "json"

    # Topic construction: captia/{env}/{tenant}/{site}/{device}/telemetry/{name}
    captia_prefix: str = "captia"
    captia_env: str = "dev"
    captia_tenant: str = "default"
    captia_site: str = ""
    captia_version: str = ""  # e.g. "v1" — empty = no version segment


class MQTTSinkAdapter:
    """MQTT sink — publishes DataPoints as JSON to captia/{env}/... topic."""

    def __init__(self, config: MQTTSinkConfig):
        self._config = config
        self._client = None
        self._connected = False
        self._published_count = 0

    @property
    def name(self) -> str:
        return "mqtt"

    def open(self) -> None:
        try:
            import paho.mqtt.client as mqtt
        except ImportError:
            raise ImportError("paho-mqtt required: pip install paho-mqtt>=2.0")

        from urllib.parse import urlparse
        parsed = urlparse(self._config.broker_url)
        host = parsed.hostname or "localhost"
        port = parsed.port or 1883

        client_id = self._config.client_id or f"synth-gen-{int(time.time())}"
        self._client = mqtt.Client(client_id=client_id)

        def on_connect(client, userdata, flags, rc):
            self._connected = rc == 0

        self._client.on_connect = on_connect
        self._client.connect(host, port, keepalive=60)
        self._client.loop_start()

        # Wait for connection
        for _ in range(50):
            if self._connected:
                break
            time.sleep(0.1)

    def emit(self, point: DataPoint) -> None:
        if not self._connected or self._client is None:
            return
        topic = self._build_topic(point)
        payload = self._build_json_payload(point)
        if payload:
            self._client.publish(topic, payload, qos=self._config.qos)
            self._published_count += 1

    def emit_batch(self, points: list[DataPoint]) -> int:
        count = 0
        for p in points:
            self.emit(p)
            count += 1
        return count

    def flush(self) -> None:
        pass

    def close(self) -> None:
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            self._client = None
            self._connected = False

    # -----------------------------------------------------------------------
    # Topic construction
    # -----------------------------------------------------------------------

    def _build_topic(self, point: DataPoint) -> str:
        """Build topic: captia/{env}/{tenant}/{site}/{device}/telemetry/{name}.

        Uses DataPoint.domain_id / site_id when available, falls back to config.
        This way synthetic data enters the same pipeline as real devices.
        """
        c = self._config
        segments = [c.captia_prefix]
        if c.captia_version:
            segments.append(c.captia_version)
        # Prefer DataPoint values (set by domain adapter) over config
        tenant = point.domain_id or c.captia_tenant or "default"
        site = point.site_id or c.captia_site or "default"
        segments += [c.captia_env, tenant, site, point.asset_id, "telemetry", point.variable]
        return "/".join(segments)

    # -----------------------------------------------------------------------
    # Payload construction
    # -----------------------------------------------------------------------

    def _build_json_payload(self, point: DataPoint) -> Optional[str]:
        """Build JSON payload: {"value": X, "ts_ns": N}.

        - Booleans are converted to 1.0/0.0 (matches captia_point float schema).
        - String values are dropped (can't be stored as float in captia_point).
        - Timestamp is included as ts_ns so Telegraf preserves it (backfill support).
        """
        if point.value is None:
            return None
        value = point.value
        if isinstance(value, bool):
            value = 1.0 if value else 0.0
        elif isinstance(value, str):
            return None
        ts_ns = self._timestamp_ns(point)
        return json.dumps({"value": value, "ts_ns": ts_ns})

    def _timestamp_ns(self, point: DataPoint) -> int:
        """Convert DataPoint timestamp to nanoseconds."""
        if hasattr(point.timestamp, 'timestamp'):
            return int(point.timestamp.timestamp() * 1e9)
        return int(pd.Timestamp(point.timestamp).timestamp() * 1e9)

    @property
    def published_count(self) -> int:
        return self._published_count
