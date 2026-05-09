"""Separator model for Industrial Refrigeration.

Implements liquid/vapor separation dynamics and pressure monitoring.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class SeparatorState:
    """State of a separator vessel.

    Attributes:
        separator_id: Separator identifier ('ALTA' or 'BAJA')
        separator_level: Liquid level (%)
        separator_pressure: Internal pressure (bar)
        separator_temperature: Temperature (°C)
        dp_pump_b1: Differential pressure pump B1 (bar)
        dp_pump_b2: Differential pressure pump B2 (bar)
    """
    separator_id: str
    separator_level: float = 50.0
    separator_pressure: float = 3.0
    separator_temperature: float = -20.0
    dp_pump_b1: float = 1.0
    dp_pump_b2: float = 1.0


class SeparatorSimulator:
    """Simulator for separator vessel dynamics.

    Implements:
    - Level dynamics based on system activity
    - Pressure correlation with rack operation
    - Differential pressure monitoring
    """

    def __init__(self, cfg: dict[str, Any], rng: np.random.Generator):
        """Initialize separator simulator.

        Args:
            cfg: Separator configuration
            rng: NumPy random generator
        """
        self.cfg = cfg
        self.rng = rng

        level_cfg = cfg.get("level_dynamics", {})
        self.base_drift_per_hour = float(level_cfg.get("base_drift_per_hour", 0.02))
        self.activity_gain = float(level_cfg.get("activity_gain", 0.20))
        self.level_noise = float(level_cfg.get("noise_sigma", 0.5))

        dp_cfg = cfg.get("dp_dynamics", {})
        self.fouling_per_day = float(dp_cfg.get("fouling_random_walk_per_day", 0.02))
        self.pump_on_gain = float(dp_cfg.get("pump_on_gain", 0.25))
        self.dp_noise = float(dp_cfg.get("noise_sigma_bar", 0.02))

    def init_state(self, separator_id: str, is_high_side: bool = True) -> SeparatorState:
        """Initialize separator state.

        Args:
            separator_id: Separator identifier
            is_high_side: True for high-pressure separator

        Returns:
            Initial separator state
        """
        if is_high_side:
            base_pressure = 15.0
            base_temp = 10.0
        else:
            base_pressure = 3.0
            base_temp = -25.0

        return SeparatorState(
            separator_id=separator_id,
            separator_level=50.0 + self.rng.normal(0, 5),
            separator_pressure=base_pressure + self.rng.normal(0, 0.5),
            separator_temperature=base_temp + self.rng.normal(0, 2),
            dp_pump_b1=1.0 + self.rng.normal(0, 0.1),
            dp_pump_b2=1.0 + self.rng.normal(0, 0.1),
        )

    def step(
        self,
        state: SeparatorState,
        dt_minutes: float,
        system_activity: float,
        pump_b1_on: bool,
        pump_b2_on: bool,
        rack_pressure: float
    ) -> SeparatorState:
        """Advance separator simulation by one timestep.

        Args:
            state: Current separator state
            dt_minutes: Time step in minutes
            system_activity: Overall system activity level (0-1)
            pump_b1_on: Pump B1 running status
            pump_b2_on: Pump B2 running status
            rack_pressure: Reference pressure from rack

        Returns:
            Updated separator state
        """
        dt_hours = dt_minutes / 60

        # Level dynamics
        # Level rises with activity, falls when pumps run
        pump_effect = -2.0 * ((1 if pump_b1_on else 0) + (1 if pump_b2_on else 0))
        activity_effect = self.activity_gain * system_activity * 10

        d_level = (
            self.base_drift_per_hour * dt_hours
            + activity_effect * dt_hours
            + pump_effect * dt_hours
            + self.rng.normal(0, self.level_noise * np.sqrt(dt_hours))
        )

        new_level = state.separator_level + d_level
        new_level = float(np.clip(new_level, 10, 95))

        # Pressure follows rack with lag
        alpha = dt_minutes / 30  # 30-minute time constant
        alpha = min(alpha, 1.0)
        new_pressure = state.separator_pressure + alpha * (rack_pressure * 0.8 - state.separator_pressure)
        new_pressure += self.rng.normal(0, 0.05)
        new_pressure = float(np.clip(new_pressure, 0.5, 40))

        # Temperature correlates with pressure (simplified)
        # Lower pressure = lower saturation temperature
        if "ALTA" in state.separator_id.upper():
            base_temp = 10.0 + 0.5 * (new_pressure - 15)
        else:
            base_temp = -25.0 + 2.0 * (new_pressure - 3)

        new_temp = base_temp + self.rng.normal(0, 0.3)
        new_temp = float(np.clip(new_temp, -50, 80))

        # Differential pressure dynamics
        # Slight fouling drift + pump effect
        dt_days = dt_minutes / 1440

        d_dp1 = (
            self.fouling_per_day * dt_days * self.rng.standard_normal()
            + (self.pump_on_gain if pump_b1_on else 0)
            + self.rng.normal(0, self.dp_noise)
        )
        d_dp2 = (
            self.fouling_per_day * dt_days * self.rng.standard_normal()
            + (self.pump_on_gain if pump_b2_on else 0)
            + self.rng.normal(0, self.dp_noise)
        )

        new_dp1 = state.dp_pump_b1 + d_dp1
        new_dp2 = state.dp_pump_b2 + d_dp2

        # Clamp and add mean reversion for stability
        new_dp1 = float(np.clip(new_dp1 * 0.99 + 1.0 * 0.01, 0.1, 5.0))
        new_dp2 = float(np.clip(new_dp2 * 0.99 + 1.0 * 0.01, 0.1, 5.0))

        return SeparatorState(
            separator_id=state.separator_id,
            separator_level=new_level,
            separator_pressure=new_pressure,
            separator_temperature=new_temp,
            dp_pump_b1=new_dp1,
            dp_pump_b2=new_dp2,
        )
