from datetime import datetime, timedelta

import numpy as np
import pytest

from bms_calibration.faults import FaultInjector, FaultType


@pytest.fixture
def injector(rng: np.random.Generator, fault_config: dict) -> FaultInjector:
    return FaultInjector(rng=rng, config=fault_config, seed=42)


@pytest.mark.unit
def test_fault_types_count() -> None:
    assert len(FaultType) == 4
    assert {ft.value for ft in FaultType} == {
        "sensor_drift",
        "valve_stuck",
        "fan_failure",
        "refrigerant_low",
    }


@pytest.mark.unit
def test_fault_injector_deterministic(fault_config: dict) -> None:
    a = FaultInjector(rng=np.random.default_rng(42), config=fault_config, seed=42)
    b = FaultInjector(rng=np.random.default_rng(42), config=fault_config, seed=42)
    start = datetime(2025, 9, 15)
    timestamps = [start + timedelta(seconds=5 * i) for i in range(2000)]
    out_a = list(a.inject(timestamps, asset_id="AULA01"))
    out_b = list(b.inject(timestamps, asset_id="AULA01"))
    assert out_a == out_b


@pytest.mark.unit
def test_fault_injector_emits_within_known_types(injector: FaultInjector) -> None:
    # 5 días con probabilidades elevadas dan algún evento
    cfg_high = {
        "valve_stuck": {"probability_per_day": 1.0, "duration_minutes": 30},
    }
    inj = FaultInjector(rng=np.random.default_rng(42), config=cfg_high, seed=42)
    start = datetime(2025, 9, 15)
    timestamps = [start + timedelta(seconds=5 * i) for i in range(86400)]
    events = list(inj.inject(timestamps, asset_id="AULA01"))
    assert len(events) >= 1
    assert all(ev.fault_type == FaultType.VALVE_STUCK for ev in events)
    assert all(ev.asset_id == "AULA01" for ev in events)
    assert all(0.3 <= ev.severity <= 1.0 for ev in events)


@pytest.mark.unit
def test_fault_injector_empty_timestamps(injector: FaultInjector) -> None:
    events = list(injector.inject([], asset_id="AULA01"))
    assert events == []
