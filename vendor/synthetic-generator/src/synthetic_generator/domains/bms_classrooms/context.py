"""Context builder for BMS Classrooms domain.

Creates simulation context with calendar, schedule, and shared environment.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np
import pandas as pd

from ...calendar_generator import build_calendar_spec, school_mask, CalendarSpec
from ...schedule_generator import build_slots, occupancy_probability, Slot
from .physics.environment import outdoor_temperature, daylight_lux


@dataclass
class BMSClassroomsContext:
    """Simulation context for BMS Classrooms domain.

    Contains shared state used across all classroom simulations.

    Attributes:
        time_index: Time points for simulation
        calendar_spec: School calendar specification
        school_mask: Boolean mask for school hours
        slots: Schedule slots with occupancy probabilities
        occupancy_probability: Per-timestamp occupancy probability
        outdoor_temp: Outdoor temperature series
        daylight_lux: Daylight illuminance series
        schedule_cfg: Schedule configuration dict
        physics_cfg: Physics configuration dict
        rng: NumPy random generator
    """
    time_index: pd.DatetimeIndex
    calendar_spec: CalendarSpec
    school_mask: pd.Series
    slots: list[Slot]
    occupancy_probability: pd.Series
    outdoor_temp: pd.Series
    daylight_lux: pd.Series
    schedule_cfg: dict[str, Any]
    physics_cfg: dict[str, Any]
    rng: np.random.Generator


def build_bms_context(
    time_index: pd.DatetimeIndex,
    project_cfg: dict[str, Any],
    domain_cfg: dict[str, Any],
    rng: np.random.Generator
) -> BMSClassroomsContext:
    """Build simulation context for BMS Classrooms domain.

    Args:
        time_index: Time points for simulation
        project_cfg: Project-level configuration
        domain_cfg: Domain-specific configuration
        rng: NumPy random generator

    Returns:
        BMSClassroomsContext with all shared state
    """
    # Build calendar specification
    calendar_cfg = domain_cfg.get("calendar", {})
    cal_spec = build_calendar_spec(calendar_cfg)

    # Build school mask
    mask_school = school_mask(time_index, cal_spec)

    # Build schedule slots
    schedule_cfg = domain_cfg.get("schedule", {})
    slots = build_slots(schedule_cfg)

    # Build occupancy probability
    p_occ = occupancy_probability(time_index, mask_school, slots)

    # Generate shared environment
    physics_cfg = domain_cfg.get("physics", {})
    outdoor_cfg = physics_cfg.get("outdoor_temp", {
        "mean_annual": 17.0,
        "amplitude": 9.5,
        "daily_noise_std": 1.0
    })
    out_temp = outdoor_temperature(time_index, outdoor_cfg, rng)
    daylight = daylight_lux(time_index)

    return BMSClassroomsContext(
        time_index=time_index,
        calendar_spec=cal_spec,
        school_mask=mask_school,
        slots=slots,
        occupancy_probability=p_occ,
        outdoor_temp=out_temp,
        daylight_lux=daylight,
        schedule_cfg=schedule_cfg,
        physics_cfg=physics_cfg,
        rng=rng
    )
