"""Prometheus metrics for BMS data generator."""

from __future__ import annotations

from prometheus_client import Counter, Gauge, generate_latest

MESSAGES_PUBLISHED = Counter(
    "captia_bms_messages_published_total",
    "Total messages published to MQTT broker",
    ["topic"],
)
PUBLISH_ERRORS = Counter(
    "captia_bms_publish_errors_total",
    "Total publish errors",
    ["topic", "reason"],
)
POINTS_GENERATED = Counter(
    "captia_bms_points_generated_total",
    "Total DataPoints generated",
    ["domain", "asset"],
)
FAULTS_INJECTED = Counter(
    "captia_bms_faults_injected_total",
    "Total fault events injected",
    ["fault_type"],
)
DUMP_EXPORT_SECONDS = Counter(
    "captia_bms_dump_export_seconds",
    "Cumulative seconds spent on dump exports",
    ["format"],
)
UPTIME_SECONDS = Gauge(
    "captia_bms_uptime_seconds",
    "Service uptime in seconds",
)
CONNECTED = Gauge(
    "captia_bms_connected",
    "Connection status to MQTT (0/1)",
)
ACTIVE_JOBS = Gauge(
    "captia_bms_active_jobs",
    "Number of active generator jobs",
)


def record_publish(topic: str, count: int = 1) -> None:
    MESSAGES_PUBLISHED.labels(topic=topic).inc(count)


def record_publish_error(topic: str, reason: str) -> None:
    PUBLISH_ERRORS.labels(topic=topic, reason=reason).inc()


def record_points(domain: str, asset: str, count: int) -> None:
    POINTS_GENERATED.labels(domain=domain, asset=asset).inc(count)


def record_fault(fault_type: str) -> None:
    FAULTS_INJECTED.labels(fault_type=fault_type).inc()


def metrics_text() -> bytes:
    return generate_latest()
