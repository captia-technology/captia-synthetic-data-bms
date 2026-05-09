"""Time index construction and temporal feature extraction."""
from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd


def build_time_index(
    start: str | datetime,
    end: str | datetime,
    freq: str,
    timezone: str = "UTC",
) -> pd.DatetimeIndex:
    """
    Build a pandas DatetimeIndex for simulation.

    Args:
        start: Start datetime (ISO string or datetime object)
        end: End datetime (ISO string or datetime object)
        freq: Frequency string (e.g., '5min', '1h', '1D')
        timezone: Timezone string (default: 'UTC')

    Returns:
        Timezone-aware DatetimeIndex
    """
    idx = pd.date_range(
        start=start, end=end, freq=freq, tz=timezone,
        nonexistent="shift_forward", ambiguous=True,
    )
    return idx


def get_dt_seconds(time_index: pd.DatetimeIndex) -> pd.Series:
    """
    Get time delta in seconds from first timestamp.

    Args:
        time_index: DatetimeIndex

    Returns:
        Series of float seconds
    """
    t0 = time_index[0]
    return (time_index - t0).total_seconds()


def get_dt_minutes(time_index: pd.DatetimeIndex) -> pd.Series:
    """
    Get time delta in minutes from first timestamp.

    Args:
        time_index: DatetimeIndex

    Returns:
        Series of float minutes
    """
    return get_dt_seconds(time_index) / 60.0


def get_hour_of_day(time_index: pd.DatetimeIndex) -> pd.Series:
    """
    Extract hour of day (0-23) from time index.

    Args:
        time_index: DatetimeIndex

    Returns:
        Series of integers (0-23)
    """
    return pd.Series(time_index.hour, index=time_index)


def get_day_of_week(time_index: pd.DatetimeIndex) -> pd.Series:
    """
    Extract day of week (0=Monday, 6=Sunday) from time index.

    Args:
        time_index: DatetimeIndex

    Returns:
        Series of integers (0-6)
    """
    return pd.Series(time_index.dayofweek, index=time_index)


def get_day_of_year(time_index: pd.DatetimeIndex) -> pd.Series:
    """
    Extract day of year (1-366) from time index.

    Args:
        time_index: DatetimeIndex

    Returns:
        Series of integers (1-366)
    """
    return pd.Series(time_index.dayofyear, index=time_index)
