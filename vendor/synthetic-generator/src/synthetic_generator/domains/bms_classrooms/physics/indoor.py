"""Indoor environment models for BMS Classrooms.

Provides simulation of temperature, CO2, humidity, noise, and illuminance.
"""
from __future__ import annotations

from typing import Dict, Any

import numpy as np
import pandas as pd


def simulate_indoor_temperature(
    index: pd.DatetimeIndex,
    outdoor_temp: pd.Series,
    occupancy: pd.Series,
    setpoint: pd.Series,
    hvac_enable: pd.Series,
    cfg_indoor: Dict[str, Any],
    rng: np.random.Generator
) -> pd.Series:
    """Simulate indoor temperature dynamics.

    First-order thermal model with HVAC control and occupancy heat gain.

    Args:
        index: Time index
        outdoor_temp: Outdoor temperature series
        occupancy: Occupancy count series
        setpoint: Temperature setpoint series
        hvac_enable: HVAC enable signal series
        cfg_indoor: Indoor physics configuration
        rng: NumPy random generator

    Returns:
        Series of indoor temperatures in °C
    """
    tau = float(cfg_indoor.get("tau_minutes", 90))
    initial = float(cfg_indoor.get("initial_temp", 20.5))
    gain = float(cfg_indoor.get("occupancy_heat_gain_c_per_person", 0.02))

    dt_min = (index[1] - index[0]).total_seconds() / 60.0 if len(index) > 1 else 5.0
    alpha = dt_min / max(1.0, tau)

    T = np.zeros(len(index), dtype=float)
    T[0] = initial + rng.normal(0, 0.4)

    for i in range(1, len(index)):
        occ_gain = gain * occupancy.iat[i]
        # Target: when HVAC enabled, move to setpoint; else drift toward outdoor
        if hvac_enable.iat[i] == 1:
            target = setpoint.iat[i] + occ_gain
        else:
            target = 0.7 * T[i - 1] + 0.3 * outdoor_temp.iat[i] + occ_gain
        T[i] = T[i - 1] + alpha * (target - T[i - 1]) + rng.normal(0, 0.05)

    return pd.Series(T, index=index, name="temperature")


def simulate_co2(
    index: pd.DatetimeIndex,
    occupancy: pd.Series,
    hvac_enable: pd.Series,
    cfg_co2: Dict[str, Any],
    rng: np.random.Generator
) -> pd.Series:
    """Simulate CO2 concentration dynamics.

    Models CO2 buildup from occupants and removal from ventilation.

    Args:
        index: Time index
        occupancy: Occupancy count series
        hvac_enable: HVAC enable signal series
        cfg_co2: CO2 physics configuration
        rng: NumPy random generator

    Returns:
        Series of CO2 concentrations in ppm
    """
    outdoor = float(cfg_co2.get("outdoor_ppm", 420))
    gen = float(cfg_co2.get("gen_ppm_per_min_per_person", 7.5))
    vent_k = float(cfg_co2.get("vent_k_per_min", 0.06))
    leak_k = float(cfg_co2.get("leak_k_per_min", 0.01))

    dt_min = (index[1] - index[0]).total_seconds() / 60.0 if len(index) > 1 else 5.0

    c = np.zeros(len(index), dtype=float)
    c[0] = outdoor + rng.normal(0, 15)

    for i in range(1, len(index)):
        occ = occupancy.iat[i]
        # Ventilation stronger when HVAC enabled
        k = leak_k + (vent_k if hvac_enable.iat[i] == 1 else 0.0)
        dc = dt_min * (occ * gen - k * (c[i - 1] - outdoor))
        c[i] = c[i - 1] + dc + rng.normal(0, 3.0)
        c[i] = float(np.clip(c[i], outdoor, 2200))

    return pd.Series(c, index=index, name="co2")


def simulate_humidity(
    index: pd.DatetimeIndex,
    outdoor_temp: pd.Series,
    occupancy: pd.Series,
    cfg_h: Dict[str, Any],
    rng: np.random.Generator,
    hvac_enable: pd.Series | None = None,
    hvac_mode: pd.Series | None = None,
) -> pd.Series:
    """Simulate relative humidity dynamics.

    Models humidity response to occupancy with first-order dynamics. When
    ``hvac_enable`` and ``hvac_mode`` are provided and the unit is in cooling
    mode, the cold coil condenses water vapor and the target RH is pulled
    down by ``cooling_dehum_delta`` (% RH). Defaults preserve legacy behavior
    when the new params are ``None`` (L-PV-09 / PATCH 003).

    Args:
        index: Time index
        outdoor_temp: Outdoor temperature series (unused but kept for API)
        occupancy: Occupancy count series
        cfg_h: Humidity physics configuration
        rng: NumPy random generator
        hvac_enable: Optional HVAC enable signal series (0/1). If ``None``,
            no dehumidification is applied (legacy).
        hvac_mode: Optional HVAC mode series ('off'/'heat'/'cool'/'auto'). If
            ``None``, no dehumidification is applied (legacy).

    Returns:
        Series of relative humidity in %RH
    """
    outdoor_mean = float(cfg_h.get("outdoor_mean", 55))
    occ_gain = float(cfg_h.get("occupancy_gain_per_person", 0.08))
    tau_minutes = float(cfg_h.get("tau_minutes", 180))
    cooling_dehum_delta = float(cfg_h.get("cooling_dehum_delta", 8.0))

    dt_min = (index[1] - index[0]).total_seconds() / 60.0 if len(index) > 1 else 5.0
    alpha = dt_min / max(1.0, tau_minutes)

    h = np.zeros(len(index), dtype=float)
    h[0] = outdoor_mean + rng.normal(0, 4)

    cool_mask: np.ndarray | None = None
    if hvac_enable is not None and hvac_mode is not None:
        cool_mask = (hvac_enable.values == 1) & (hvac_mode.values == "cool")

    for i in range(1, len(index)):
        target = outdoor_mean + occ_gain * occupancy.iat[i]
        if cool_mask is not None and cool_mask[i]:
            target -= cooling_dehum_delta
        h[i] = h[i - 1] + alpha * (target - h[i - 1]) + rng.normal(0, 0.2)

    return pd.Series(np.clip(h, 10, 90), index=index, name="humidity")


def simulate_noise(
    index: pd.DatetimeIndex,
    occupancy: pd.Series,
    cfg_noise: Dict[str, Any],
    rng: np.random.Generator
) -> pd.Series:
    """Simulate noise levels.

    Models ambient noise based on occupancy.

    Args:
        index: Time index
        occupancy: Occupancy count series
        cfg_noise: Noise physics configuration
        rng: NumPy random generator

    Returns:
        Series of noise levels in dB(A)
    """
    base_u = float(cfg_noise.get("base_unoccupied", 33))
    base_o = float(cfg_noise.get("base_occupied", 55))
    std = float(cfg_noise.get("std", 4))

    n = np.where(
        occupancy.values > 0,
        base_o + 0.35 * occupancy.values,
        base_u
    ) + rng.normal(0, std, size=len(index))

    return pd.Series(np.clip(n, 25, 90), index=index, name="noise")


def simulate_illuminance(
    index: pd.DatetimeIndex,
    daylight_lux: pd.Series,
    light_state: pd.Series,
    cfg_light: Dict[str, Any],
    rng: np.random.Generator
) -> pd.Series:
    """Simulate indoor illuminance.

    Combines daylight and artificial lighting.

    Args:
        index: Time index
        daylight_lux: Daylight illuminance series
        light_state: Light on/off state series
        cfg_light: Lighting physics configuration
        rng: NumPy random generator

    Returns:
        Series of illuminance in lux
    """
    target_on = float(cfg_light.get("target_lux_on", 550))
    target_off = float(cfg_light.get("target_lux_off", 70))
    std = float(cfg_light.get("std", 40))

    base = np.where(
        light_state.values == 1,
        np.maximum(daylight_lux.values, target_on),
        np.maximum(daylight_lux.values, target_off)
    )
    lux = base + rng.normal(0, std, size=len(index))

    return pd.Series(np.clip(lux, 0, 2500), index=index, name="illuminance")


def derive_pir_presence(
    occupancy: pd.Series,
    rng: np.random.Generator
) -> pd.Series:
    """Derive PIR presence detection from occupancy.

    Models PIR sensor with false positives and negatives.

    Args:
        occupancy: Occupancy count series
        rng: NumPy random generator

    Returns:
        Series of PIR presence (0/1)
    """
    present = occupancy.values > 0
    fp = rng.random(len(occupancy)) < 0.004
    fn = (rng.random(len(occupancy)) < 0.01) & present
    val = (present | fp) & (~fn)

    return pd.Series(val.astype(int), index=occupancy.index, name="presence_pir")
