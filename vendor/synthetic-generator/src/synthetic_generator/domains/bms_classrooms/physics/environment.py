"""Environmental models for BMS Classrooms.

Provides outdoor temperature and daylight simulation.
"""
from __future__ import annotations

from typing import Dict, Any

import numpy as np
import pandas as pd


def outdoor_temperature(
    index: pd.DatetimeIndex,
    cfg: Dict[str, Any],
    rng: np.random.Generator
) -> pd.Series:
    """Generate outdoor temperature time series.

    Simple seasonal sinusoidal model with daily noise variation.

    Args:
        index: Time index
        cfg: Configuration dict with mean_annual, amplitude, daily_noise_std
        rng: NumPy random generator

    Returns:
        Series of outdoor temperatures in °C
    """
    mean_annual = float(cfg.get("mean_annual", 17.0))
    amp = float(cfg.get("amplitude", 9.5))
    noise_std = float(cfg.get("daily_noise_std", 1.0))

    doy = index.dayofyear.values
    # Peak around late July (day 200)
    seasonal = mean_annual + amp * np.sin(2 * np.pi * (doy - 200) / 365.25)

    # Add smooth daily variability (correlated)
    daily = rng.normal(0, noise_std, size=len(index))
    # Smooth with EWMA-ish filter
    alpha = 0.02
    smooth = np.zeros(len(index))
    for i in range(len(index)):
        smooth[i] = daily[i] if i == 0 else alpha * daily[i] + (1 - alpha) * smooth[i - 1]

    return pd.Series(seasonal + smooth, index=index, name="outdoor_temp")


def daylight_lux(index: pd.DatetimeIndex) -> pd.Series:
    """Generate daylight illuminance time series.

    Approximates daylight levels with seasonal day length variation.
    Returns indoor daylight levels near windows (peak ~700 lux).

    Args:
        index: Time index

    Returns:
        Series of daylight illuminance in lux
    """
    hour = index.hour.values + index.minute.values / 60.0
    doy = index.dayofyear.values

    # Day length: ~9h winter to ~15h summer
    daylen = 12 + 3 * np.sin(2 * np.pi * (doy - 172) / 365.25)  # Max around June 21
    sunrise = 12 - daylen / 2
    sunset = 12 + daylen / 2

    lux = np.zeros(len(index))
    for i in range(len(index)):
        if hour[i] < sunrise[i] or hour[i] > sunset[i]:
            lux[i] = 0.0
        else:
            # Cosine curve within daylight hours
            phase = (hour[i] - sunrise[i]) / (sunset[i] - sunrise[i])  # 0..1
            # Peak ~ 700 lux as "indoor daylight near windows"
            lux[i] = 700 * np.sin(np.pi * phase) ** 1.2

    return pd.Series(lux, index=index, name="daylight_lux")
