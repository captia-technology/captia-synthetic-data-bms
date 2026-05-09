"""Meteorological driver for Industrial Refrigeration.

Provides outdoor weather conditions that drive condenser performance.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd


@dataclass
class MeteoDriver:
    """Weather data driver for simulation.

    Can use synthetic generation or replay from file.

    Attributes:
        time_index: Time points for weather data
        temperature_2m: Outdoor temperature series (°C)
        relative_humidity_2m: Relative humidity series (%)
        precipitation: Precipitation series (mm)
        wind_speed_10m: Wind speed series (m/s)
        wind_direction_10m: Wind direction series (degrees)
    """
    time_index: pd.DatetimeIndex
    temperature_2m: pd.Series
    relative_humidity_2m: pd.Series
    precipitation: pd.Series
    wind_speed_10m: pd.Series
    wind_direction_10m: pd.Series

    def get_at(self, timestamp: pd.Timestamp) -> dict[str, float]:
        """Get weather conditions at a specific timestamp."""
        idx = self.time_index.get_indexer([timestamp], method="nearest")[0]
        return {
            "outdoor_temperature_2m": float(self.temperature_2m.iloc[idx]),
            "outdoor_relative_humidity_2m": float(self.relative_humidity_2m.iloc[idx]),
            "outdoor_precipitation": float(self.precipitation.iloc[idx]),
            "outdoor_wind_speed_10m": float(self.wind_speed_10m.iloc[idx]),
            "outdoor_wind_direction_10m": float(self.wind_direction_10m.iloc[idx]),
        }


def generate_synthetic_weather(
    time_index: pd.DatetimeIndex,
    cfg: dict[str, Any],
    rng: np.random.Generator
) -> MeteoDriver:
    """Generate synthetic weather data.

    Creates realistic weather patterns for a Mediterranean climate
    (southeastern Spain).

    Args:
        time_index: Time points for weather generation
        cfg: Weather configuration
        rng: NumPy random generator

    Returns:
        MeteoDriver with synthetic weather data
    """
    n = len(time_index)
    doy = time_index.dayofyear.values
    hour = time_index.hour.values + time_index.minute.values / 60.0

    # Temperature: seasonal + diurnal variation
    # Mean annual ~18°C, amplitude ~10°C for SE Spain
    mean_annual = cfg.get("mean_annual_temp", 18.0)
    seasonal_amp = cfg.get("seasonal_amplitude", 10.0)
    diurnal_amp = cfg.get("diurnal_amplitude", 8.0)

    # Seasonal component (peak in July)
    seasonal = mean_annual + seasonal_amp * np.sin(2 * np.pi * (doy - 200) / 365.25)

    # Diurnal component (peak at 14:00)
    diurnal = diurnal_amp * np.sin(2 * np.pi * (hour - 14) / 24)

    # Weather systems (slow-moving fronts)
    weather_noise = _generate_correlated_noise(n, correlation=0.98, scale=3.0, rng=rng)

    temperature = seasonal + diurnal + weather_noise
    temperature = np.clip(temperature, -5, 45)

    # Relative humidity: inversely correlated with temperature
    base_humidity = 65 - 0.8 * (temperature - mean_annual)
    humidity_noise = _generate_correlated_noise(n, correlation=0.95, scale=8.0, rng=rng)
    humidity = base_humidity + humidity_noise
    humidity = np.clip(humidity, 15, 98)

    # Precipitation: sporadic events
    precip = np.zeros(n)
    rain_prob = 0.02  # ~2% chance per timestep
    rain_events = rng.random(n) < rain_prob
    precip[rain_events] = rng.exponential(2.0, size=np.sum(rain_events))
    precip = np.clip(precip, 0, 50)

    # Wind speed: gamma distribution
    wind_mean = cfg.get("wind_mean", 3.0)
    wind_shape = 2.0
    wind_scale = wind_mean / wind_shape
    wind_speed = rng.gamma(wind_shape, wind_scale, size=n)
    wind_speed = np.clip(wind_speed, 0, 25)

    # Wind direction: prevailing + random
    prevailing = cfg.get("prevailing_wind_direction", 270)  # West
    wind_direction = (prevailing + rng.normal(0, 45, size=n)) % 360

    return MeteoDriver(
        time_index=time_index,
        temperature_2m=pd.Series(temperature, index=time_index, name="outdoor_temperature_2m"),
        relative_humidity_2m=pd.Series(humidity, index=time_index, name="outdoor_relative_humidity_2m"),
        precipitation=pd.Series(precip, index=time_index, name="outdoor_precipitation"),
        wind_speed_10m=pd.Series(wind_speed, index=time_index, name="outdoor_wind_speed_10m"),
        wind_direction_10m=pd.Series(wind_direction, index=time_index, name="outdoor_wind_direction_10m"),
    )


def load_weather_from_file(
    time_index: pd.DatetimeIndex,
    file_path: Path,
    cfg: dict[str, Any]
) -> MeteoDriver:
    """Load weather data from CSV file.

    Args:
        time_index: Target time index for interpolation
        file_path: Path to weather CSV file
        cfg: Configuration for column mapping

    Returns:
        MeteoDriver with loaded weather data
    """
    df = pd.read_csv(file_path, parse_dates=["timestamp"])
    df.set_index("timestamp", inplace=True)

    # Reindex to target time index with interpolation
    df_reindexed = df.reindex(time_index, method="nearest")

    return MeteoDriver(
        time_index=time_index,
        temperature_2m=df_reindexed.get("outdoor_temperature_2m", pd.Series(20.0, index=time_index)),
        relative_humidity_2m=df_reindexed.get("outdoor_relative_humidity_2m", pd.Series(50.0, index=time_index)),
        precipitation=df_reindexed.get("outdoor_precipitation", pd.Series(0.0, index=time_index)),
        wind_speed_10m=df_reindexed.get("outdoor_wind_speed_10m", pd.Series(3.0, index=time_index)),
        wind_direction_10m=df_reindexed.get("outdoor_wind_direction_10m", pd.Series(180.0, index=time_index)),
    )


def _generate_correlated_noise(
    n: int,
    correlation: float,
    scale: float,
    rng: np.random.Generator
) -> np.ndarray:
    """Generate temporally correlated noise using AR(1) process."""
    noise = np.zeros(n)
    innovation = rng.normal(0, scale * np.sqrt(1 - correlation**2), size=n)
    noise[0] = rng.normal(0, scale)
    for i in range(1, n):
        noise[i] = correlation * noise[i-1] + innovation[i]
    return noise
