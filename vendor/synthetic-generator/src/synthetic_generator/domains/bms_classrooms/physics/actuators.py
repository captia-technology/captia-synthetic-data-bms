"""Actuator models for BMS Classrooms.

Provides HVAC and lighting control simulation.
"""
from __future__ import annotations

from typing import Dict, Any

import numpy as np
import pandas as pd


def derive_scene(
    index: pd.DatetimeIndex,
    occupancy: pd.Series,
    school_mask: pd.Series,
    rng: np.random.Generator
) -> pd.Series:
    """Derive scene state from occupancy and schedule.

    Scenes: 'class' during school hours with occupancy,
    'out_of_hours' otherwise, occasional 'manual' overrides.

    Args:
        index: Time index
        occupancy: Occupancy count series
        school_mask: Boolean school hours mask
        rng: NumPy random generator

    Returns:
        Series of scene states ('class', 'out_of_hours', 'manual')
    """
    scene = np.where(
        (school_mask.values) & (occupancy.values > 0),
        "class",
        "out_of_hours"
    ).astype(object)

    # Manual override: rare, short bursts
    p_start = 0.0008  # ~once per few days per aula
    in_manual = False
    remaining = 0

    for i in range(len(scene)):
        if in_manual:
            scene[i] = "manual"
            remaining -= 1
            if remaining <= 0:
                in_manual = False
            continue
        if rng.random() < p_start:
            in_manual = True
            remaining = int(rng.integers(15, 90))  # 15-90 steps
            scene[i] = "manual"

    return pd.Series(scene, index=index, name="scene_mode")


def thermostat_setpoint(
    scene: pd.Series,
    cfg_indoor: Dict[str, Any],
    rng: np.random.Generator
) -> pd.Series:
    """Generate thermostat setpoint based on scene.

    Args:
        scene: Scene state series
        cfg_indoor: Indoor physics configuration
        rng: NumPy random generator

    Returns:
        Series of temperature setpoints in °C
    """
    sp_class = float(cfg_indoor.get("setpoint_class", 21.0))
    sp_ooh = float(cfg_indoor.get("setpoint_out_of_hours", 18.0))
    # H-23 / PATCH 002: jitter configurable. Default 0.3 mantiene comportamiento previo.
    # Reducir a 0.05 vía domain.yaml limpia state_events (setpoint cambia con escena, no por sample).
    jitter_std = float(cfg_indoor.get("setpoint_jitter_std", 0.3))
    manual_jitter_std = float(cfg_indoor.get("setpoint_manual_jitter_std", 0.8))
    jitter = rng.normal(0, jitter_std, size=len(scene))

    base = np.where(scene.values == "class", sp_class, sp_ooh)
    # Manual: user may set higher or lower
    base = np.where(
        scene.values == "manual",
        base + rng.normal(0, manual_jitter_std, size=len(scene)),
        base
    )

    return pd.Series(
        np.clip(base + jitter, 16.0, 26.0),
        index=scene.index,
        name="thermostat_setpoint"
    )


def hvac_mode(
    outdoor_temp: pd.Series,
    rng: np.random.Generator
) -> pd.Series:
    """Determine HVAC mode based on outdoor temperature.

    Simple seasonal logic: heat if cold, cool if hot.

    Args:
        outdoor_temp: Outdoor temperature series
        rng: NumPy random generator

    Returns:
        Series of HVAC modes ('off', 'heat', 'cool', 'auto')
    """
    mode = np.full(len(outdoor_temp), "off", dtype=object)
    t = outdoor_temp.values

    mode[t < 16] = "heat"
    mode[t > 26] = "cool"

    # Shoulder season: some auto
    shoulder = (t >= 16) & (t <= 26)
    mode[shoulder] = np.where(rng.random(np.sum(shoulder)) < 0.15, "auto", "off")

    return pd.Series(mode, index=outdoor_temp.index, name="hvac_mode")


def hvac_enable(
    indoor_temp: pd.Series,
    setpoint: pd.Series,
    occupancy: pd.Series,
    scene: pd.Series
) -> pd.Series:
    """Determine HVAC enable state.

    Enable when: occupied class scene with error > 0.4°C, or any error > 1.5°C.

    Args:
        indoor_temp: Indoor temperature series
        setpoint: Temperature setpoint series
        occupancy: Occupancy count series
        scene: Scene state series

    Returns:
        Series of HVAC enable states (0/1)
    """
    err = np.abs(indoor_temp.values - setpoint.values)
    enable = (
        ((scene.values == "class") & (occupancy.values > 0) & (err > 0.4)) |
        (err > 1.5)
    )

    return pd.Series(enable.astype(int), index=indoor_temp.index, name="hvac_enable")


def heating_valve_position(
    indoor_temp: pd.Series,
    setpoint: pd.Series,
    mode: pd.Series
) -> pd.Series:
    """Calculate heating valve position.

    Proportional control in heating mode only.

    Args:
        indoor_temp: Indoor temperature series
        setpoint: Temperature setpoint series
        mode: HVAC mode series

    Returns:
        Series of valve positions (0-100%)
    """
    err = setpoint.values - indoor_temp.values
    pos = np.where(mode.values == "heat", np.clip(err * 35.0, 0, 100), 0.0)

    return pd.Series(pos, index=indoor_temp.index, name="heating_valve_pos")


def light_state(
    occupancy: pd.Series,
    daylight_lux: pd.Series,
    rng: np.random.Generator
) -> pd.Series:
    """Determine lighting state.

    Lights on when occupied and daylight low, with some randomness.

    Args:
        occupancy: Occupancy count series
        daylight_lux: Daylight illuminance series
        rng: NumPy random generator

    Returns:
        Series of light states (0/1)
    """
    threshold = 250
    base = (occupancy.values > 0) & (daylight_lux.values < threshold)
    # Sometimes turn on even with sufficient daylight
    extra = (
        (occupancy.values > 0) &
        (daylight_lux.values >= threshold) &
        (rng.random(len(occupancy)) < 0.12)
    )
    on = base | extra

    return pd.Series(on.astype(int), index=occupancy.index, name="light_state")
