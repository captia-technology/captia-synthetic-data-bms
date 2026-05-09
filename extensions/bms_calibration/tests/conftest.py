import numpy as np
import pytest


@pytest.fixture
def rng() -> np.random.Generator:
    return np.random.default_rng(seed=42)


@pytest.fixture
def fault_config() -> dict:
    return {
        "sensor_drift": {"probability_per_day": 0.001, "drift_rate": 0.5},
        "valve_stuck": {"probability_per_day": 0.0005, "duration_minutes": 60},
        "fan_failure": {"probability_per_day": 0.0002, "duration_minutes": 240},
        "refrigerant_low": {"probability_per_day": 0.0001, "drift_rate": 2.0},
    }
