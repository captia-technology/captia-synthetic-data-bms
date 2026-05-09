"""Energy models for BMS Classrooms.

Provides power consumption and energy integration.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def simulate_power(
    index: pd.DatetimeIndex,
    occupancy: pd.Series,
    light_state: pd.Series,
    hvac_enable: pd.Series,
    rng: np.random.Generator
) -> pd.Series:
    """Simulate power consumption.

    Simplified power model combining base load, lighting, HVAC, and occupancy.

    Args:
        index: Time index
        occupancy: Occupancy count series
        light_state: Light on/off state series
        hvac_enable: HVAC enable state series
        rng: NumPy random generator

    Returns:
        Series of power consumption in Watts
    """
    # Base load: standby equipment
    base = 80 + rng.normal(0, 10, size=len(index))

    # Lighting load
    light = light_state.values * (180 + rng.normal(0, 20, size=len(index)))

    # HVAC load
    hvac = hvac_enable.values * (900 + rng.normal(0, 120, size=len(index)))

    # Occupancy load (laptops, etc.)
    occ = occupancy.values * (8 + rng.normal(0, 1.5, size=len(index)))

    # Occasional spikes
    spikes = (rng.random(len(index)) < 0.0008) * rng.uniform(500, 1500, size=len(index))

    p = base + light + hvac + occ + spikes

    return pd.Series(np.clip(p, 0, 6000), index=index, name="power")


def integrate_energy_kwh(
    index: pd.DatetimeIndex,
    power_w: pd.Series
) -> pd.Series:
    """Integrate power to cumulative energy.

    Args:
        index: Time index
        power_w: Power consumption series in Watts

    Returns:
        Series of cumulative energy in kWh
    """
    dt_h = (index[1] - index[0]).total_seconds() / 3600.0 if len(index) > 1 else 1 / 12
    e = np.cumsum(power_w.values * dt_h) / 1000.0

    return pd.Series(e, index=index, name="energy")
