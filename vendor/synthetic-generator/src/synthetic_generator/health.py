"""
Health and Metrics Server for synthetic_generator

Provides /health and /metrics endpoints for observability.
Runs as a lightweight HTTP server in a separate thread.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Dict, Optional

LOG = logging.getLogger("synthetic_generator.health")


@dataclass
class GeneratorMetrics:
    """Metrics collected by the generator."""

    # Counters
    messages_published_total: int = 0
    publish_errors_total: int = 0
    points_generated_total: int = 0
    cycles_completed_total: int = 0
    dataset_regenerations_total: int = 0

    # Gauges
    last_publish_timestamp: Optional[datetime] = None
    last_publish_duration_ms: float = 0.0
    current_batch_size: int = 0
    connected_to_mqtt: bool = False

    # Per-topic counters (dict of topic -> count)
    messages_by_topic: Dict[str, int] = field(default_factory=dict)

    # Timing
    startup_time: datetime = field(default_factory=datetime.now)

    def increment_published(self, topic: str, count: int = 1):
        """Increment published message counters."""
        self.messages_published_total += count
        self.messages_by_topic[topic] = self.messages_by_topic.get(topic, 0) + count
        self.last_publish_timestamp = datetime.now()

    def increment_errors(self, count: int = 1):
        """Increment error counter."""
        self.publish_errors_total += count

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for JSON serialization."""
        uptime_seconds = (datetime.now() - self.startup_time).total_seconds()
        return {
            "messages_published_total": self.messages_published_total,
            "publish_errors_total": self.publish_errors_total,
            "points_generated_total": self.points_generated_total,
            "cycles_completed_total": self.cycles_completed_total,
            "dataset_regenerations_total": self.dataset_regenerations_total,
            "last_publish_timestamp": (
                self.last_publish_timestamp.isoformat() if self.last_publish_timestamp else None
            ),
            "last_publish_duration_ms": self.last_publish_duration_ms,
            "current_batch_size": self.current_batch_size,
            "connected_to_mqtt": self.connected_to_mqtt,
            "uptime_seconds": uptime_seconds,
            "messages_by_topic": self.messages_by_topic,
        }

    def to_prometheus(self) -> str:
        """Convert metrics to Prometheus text format."""
        domain = os.environ.get("GENERATOR_DOMAIN", "unknown")
        lines = [
            "# HELP captia_generator_messages_published_total Total messages published to MQTT",
            "# TYPE captia_generator_messages_published_total counter",
            f'captia_generator_messages_published_total{{domain="{domain}"}} {self.messages_published_total}',
            "",
            "# HELP captia_generator_publish_errors_total Total publish errors",
            "# TYPE captia_generator_publish_errors_total counter",
            f'captia_generator_publish_errors_total{{domain="{domain}"}} {self.publish_errors_total}',
            "",
            "# HELP captia_generator_points_generated_total Total data points generated",
            "# TYPE captia_generator_points_generated_total counter",
            f'captia_generator_points_generated_total{{domain="{domain}"}} {self.points_generated_total}',
            "",
            "# HELP captia_generator_cycles_completed_total Total publish cycles completed",
            "# TYPE captia_generator_cycles_completed_total counter",
            f'captia_generator_cycles_completed_total{{domain="{domain}"}} {self.cycles_completed_total}',
            "",
            "# HELP captia_generator_dataset_regenerations_total Total dataset regenerations",
            "# TYPE captia_generator_dataset_regenerations_total counter",
            f'captia_generator_dataset_regenerations_total{{domain="{domain}"}} {self.dataset_regenerations_total}',
            "",
            "# HELP captia_generator_last_publish_duration_ms Duration of last publish batch",
            "# TYPE captia_generator_last_publish_duration_ms gauge",
            f'captia_generator_last_publish_duration_ms{{domain="{domain}"}} {self.last_publish_duration_ms:.2f}',
            "",
            "# HELP captia_generator_connected Connected to MQTT broker",
            "# TYPE captia_generator_connected gauge",
            f'captia_generator_connected{{domain="{domain}"}} {1 if self.connected_to_mqtt else 0}',
            "",
            "# HELP captia_generator_current_batch_size Current batch size",
            "# TYPE captia_generator_current_batch_size gauge",
            f'captia_generator_current_batch_size{{domain="{domain}"}} {self.current_batch_size}',
            "",
            "# HELP captia_generator_uptime_seconds Generator uptime in seconds",
            "# TYPE captia_generator_uptime_seconds gauge",
            f'captia_generator_uptime_seconds{{domain="{domain}"}} '
            f"{(datetime.now() - self.startup_time).total_seconds():.0f}",
        ]

        # Add per-topic metrics
        if self.messages_by_topic:
            lines.extend(
                [
                    "",
                    "# HELP captia_generator_messages_by_topic_total Messages published by topic",
                    "# TYPE captia_generator_messages_by_topic_total counter",
                ]
            )
            for topic, count in self.messages_by_topic.items():
                safe_topic = topic.replace('"', '\\"')
                lines.append(
                    f'captia_generator_messages_by_topic_total{{domain="{domain}",topic="{safe_topic}"}} {count}'
                )

        return "\n".join(lines) + "\n"


@dataclass
class HealthStatus:
    """Health status information."""

    healthy: bool = True
    config_loaded: bool = False
    mqtt_connected: bool = False
    loop_running: bool = False
    last_error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "healthy": self.healthy,
            "checks": {
                "config_loaded": self.config_loaded,
                "mqtt_connected": self.mqtt_connected,
                "loop_running": self.loop_running,
            },
            "last_error": self.last_error,
        }


# Global instances (shared with publisher)
_metrics = GeneratorMetrics()
_health = HealthStatus()
_lock = threading.Lock()


def get_metrics() -> GeneratorMetrics:
    """Get the global metrics instance."""
    return _metrics


def get_health() -> HealthStatus:
    """Get the global health status instance."""
    return _health


def update_status(state: str, **extra) -> None:
    """Update the health status (backward-compatible API).

    Maps legacy state strings to HealthStatus fields.
    """
    with _lock:
        if state == "running" or state == "live":
            _health.loop_running = True
            _health.healthy = True
        elif state == "backfill":
            _health.config_loaded = True
            _health.healthy = True
        elif state == "idle":
            _health.loop_running = False
        elif state == "error":
            _health.healthy = False
            _health.last_error = extra.get("error", "unknown")

        if "domain" in extra:
            _health.config_loaded = True
        if "points_emitted" in extra:
            _metrics.points_generated_total = extra["points_emitted"]


class HealthRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for health and metrics endpoints."""

    def log_message(self, format, *args):
        """Override to suppress default logging."""
        LOG.debug("Health server: %s", format % args)

    def handle(self):
        """Handle request with error suppression for client disconnections."""
        try:
            super().handle()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/health":
            self._handle_health()
        elif self.path == "/metrics":
            self._handle_metrics()
        elif self.path == "/metrics/json":
            self._handle_metrics_json()
        elif self.path == "/":
            self._handle_root()
        else:
            self._send_response(404, "text/plain", "Not Found")

    def _handle_root(self):
        """Handle root endpoint with links."""
        content = """synthetic_generator Health Server

Endpoints:
  /health       - Health check (JSON)
  /metrics      - Prometheus metrics
  /metrics/json - Metrics as JSON
"""
        self._send_response(200, "text/plain", content)

    def _handle_health(self):
        """Handle /health endpoint."""
        with _lock:
            status = _health.to_dict()
            status["domain"] = os.environ.get("GENERATOR_DOMAIN", "unknown")
            status["timestamp"] = datetime.now().isoformat()

        code = 200 if status["healthy"] else 503
        self._send_response(code, "application/json", json.dumps(status, indent=2))

    def _handle_metrics(self):
        """Handle /metrics endpoint (Prometheus format)."""
        with _lock:
            content = _metrics.to_prometheus()
        self._send_response(200, "text/plain; version=0.0.4", content)

    def _handle_metrics_json(self):
        """Handle /metrics/json endpoint."""
        with _lock:
            content = json.dumps(_metrics.to_dict(), indent=2)
        self._send_response(200, "application/json", content)

    def _send_response(self, code: int, content_type: str, content: str):
        """Send HTTP response."""
        try:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))
        except BrokenPipeError:
            pass
        except ConnectionResetError:
            pass


class HealthServer:
    """Health server that runs in a background thread."""

    def __init__(self, port: int = 8000):
        self.port = port
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[threading.Thread] = None
        self._running = False

    def start(self):
        """Start the health server in a background thread."""
        if self._running:
            return

        try:
            self.server = HTTPServer(("0.0.0.0", self.port), HealthRequestHandler)
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            self._running = True
            LOG.info("Health server started on port %d", self.port)
        except Exception as e:
            LOG.error("Failed to start health server on port %d: %s", self.port, e)

    def _run(self):
        """Server loop (runs in background thread)."""
        if self.server:
            self.server.serve_forever()

    def stop(self):
        """Stop the health server."""
        if self.server:
            self.server.shutdown()
            self._running = False
            LOG.info("Health server stopped")


def start_health_server(port: int | None = None) -> HealthServer:
    """Start the health server.

    Args:
        port: Port to listen on (default from HEALTH_PORT env or 8000)

    Returns:
        HealthServer instance
    """
    if port is None:
        port = int(os.environ.get("HEALTH_PORT", "8000"))

    server = HealthServer(port)
    server.start()
    return server
