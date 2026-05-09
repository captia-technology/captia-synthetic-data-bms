"""Occupancy models for BMS Classrooms.

Provides classroom capacity and occupancy generation.
"""
from __future__ import annotations

from typing import Tuple

import numpy as np
import pandas as pd


def sample_aula_parameters(
    rng: np.random.Generator,
    capacity_mean: float,
    capacity_std: float,
    util_mean: float,
    util_std: float
) -> Tuple[int, float]:
    """Sample per-classroom parameters.

    Generates random capacity and utilization for a classroom.

    Args:
        rng: NumPy random generator
        capacity_mean: Mean classroom capacity
        capacity_std: Standard deviation of capacity
        util_mean: Mean utilization factor
        util_std: Standard deviation of utilization

    Returns:
        Tuple of (capacity, utilization)
    """
    capacity = int(max(10, rng.normal(capacity_mean, capacity_std)))
    util = float(np.clip(rng.normal(util_mean, util_std), 0.2, 0.98))
    return capacity, util


def generate_occupancy_count(
    index: pd.DatetimeIndex,
    p_occ: pd.Series,
    capacity: int,
    util: float,
    day_variability: float,
    rng: np.random.Generator
) -> pd.Series:
    """Generate occupancy count time series.

    Converts occupancy probability schedule to actual counts using
    Poisson sampling with daily variation.

    Args:
        index: Time index
        p_occ: Occupancy probability series (0-1)
        capacity: Classroom capacity
        util: Utilization factor
        day_variability: Day-to-day variation factor
        rng: NumPy random generator

    Returns:
        Series of occupancy counts (integer)
    """
    dates = pd.Series(index.date, index=index)
    unique_days = sorted(set(dates.values))
    day_mult = {
        d: float(np.clip(rng.normal(1.0, day_variability), 0.6, 1.4))
        for d in unique_days
    }

    occ = np.zeros(len(index), dtype=int)
    for i, ts in enumerate(index):
        p = float(p_occ.iat[i])
        if p <= 0:
            occ[i] = 0
            continue
        expected = capacity * util * p * day_mult[ts.date()]
        # Sample around expected; cap at capacity
        val = rng.poisson(lam=max(0.1, expected))
        occ[i] = int(np.clip(val, 0, capacity))

    return pd.Series(occ, index=index, name="occupancy")
