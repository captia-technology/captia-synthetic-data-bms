"""Tests for FaultEventEmitter."""

from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np

from bms_calibration import FaultEvent, FaultEventEmitter, FaultInjector, FaultType


class FakeSink:
    def __init__(self) -> None:
        self.emitted: list = []

    def emit(self, point) -> None:
        self.emitted.append(point)


def test_emit_single_event_emits_two_datapoints() -> None:
    sink = FakeSink()
    emitter = FaultEventEmitter(sink, "bms_classrooms", "ies_simarro")
    event = FaultEvent(
        fault_type=FaultType.SENSOR_DRIFT,
        asset_id="AULA01",
        start=datetime(2026, 1, 15, 10, 0),
        end=datetime(2026, 1, 16, 10, 0),
        severity=0.7,
    )
    n = emitter.emit_events([event])
    assert n == 2
    assert len(sink.emitted) == 2

    p_start, p_end = sink.emitted
    assert p_start.variable == "fault.sensor_drift"
    assert p_start.value == 0.7
    assert p_start.asset_id == "AULA01"
    assert p_start.domain_id == "bms_classrooms"
    assert p_start.site_id == "ies_simarro"
    assert p_start.timestamp == event.start
    assert p_start.origin == "synthetic_fault"

    assert p_end.variable == "fault.sensor_drift"
    assert p_end.value == 0.0
    assert p_end.timestamp == event.end


def test_emit_multiple_event_types() -> None:
    sink = FakeSink()
    emitter = FaultEventEmitter(sink, "bms_classrooms", "ies_simarro")
    events = [
        FaultEvent(
            FaultType.VALVE_STUCK, "AULA01", datetime(2026, 1, 15, 8), datetime(2026, 1, 15, 9), 1.0
        ),
        FaultEvent(
            FaultType.FAN_FAILURE,
            "AULA02",
            datetime(2026, 1, 15, 12),
            datetime(2026, 1, 15, 16),
            0.5,
        ),
        FaultEvent(
            FaultType.REFRIGERANT_LOW,
            "AULA03",
            datetime(2026, 1, 16, 9),
            datetime(2026, 1, 16, 21),
            0.3,
        ),
    ]
    n = emitter.emit_events(events)
    assert n == 6
    assert len(sink.emitted) == 6

    variables = [p.variable for p in sink.emitted]
    assert variables == [
        "fault.valve_stuck",
        "fault.valve_stuck",
        "fault.fan_failure",
        "fault.fan_failure",
        "fault.refrigerant_low",
        "fault.refrigerant_low",
    ]


def test_emit_events_accumulates_count() -> None:
    sink = FakeSink()
    emitter = FaultEventEmitter(sink, "bms_classrooms", "ies_simarro")
    event = FaultEvent(
        FaultType.SENSOR_DRIFT, "AULA01", datetime(2026, 1, 15, 10), datetime(2026, 1, 16, 10), 0.5
    )
    emitter.emit_events([event])
    emitter.emit_events([event, event])
    assert emitter.emitted_count == 6


def test_emit_handles_empty_events() -> None:
    sink = FakeSink()
    emitter = FaultEventEmitter(sink, "bms_classrooms", "ies_simarro")
    n = emitter.emit_events([])
    assert n == 0
    assert sink.emitted == []


def test_integration_with_fault_injector() -> None:
    """End-to-end: FaultInjector → FaultEventEmitter → sink with deterministic counts."""
    sink = FakeSink()
    emitter = FaultEventEmitter(sink, "bms_classrooms", "ies_simarro")

    cfg = {
        "sensor_drift": {"probability_per_day": 1.0, "duration_minutes": 1440},
        "valve_stuck": {"probability_per_day": 0.5, "duration_minutes": 60},
    }
    injector = FaultInjector(rng=np.random.default_rng(42), config=cfg, seed=42)
    timestamps = [datetime(2026, 1, 1) + timedelta(minutes=5 * i) for i in range(2880)]  # 10 days

    events = list(injector.inject(timestamps, "AULA01"))
    n_emitted = emitter.emit_events(events)

    # Each event → 2 datapoints
    assert n_emitted == 2 * len(events)
    assert len(sink.emitted) == 2 * len(events)

    # All emitted points have variable starting with "fault."
    assert all(p.variable.startswith("fault.") for p in sink.emitted)

    # All from same asset and site
    assert all(p.asset_id == "AULA01" for p in sink.emitted)
    assert all(p.site_id == "ies_simarro" for p in sink.emitted)
