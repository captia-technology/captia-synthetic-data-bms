"""Pump model for Industrial Refrigeration.

Implements lead-lag control for refrigerant circulation pumps.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from ....core.control_utils import LeadLagController, MinOnOffTimer


@dataclass
class PumpState:
    """State of the pump system.

    Attributes:
        pump_b1_high_status: Pump B1 high speed status
        pump_b1_low_status: Pump B1 low speed status
        pump_b2_high_status: Pump B2 high speed status
        pump_b2_low_status: Pump B2 low speed status
        lead_pump: Current lead pump index
    """
    pump_b1_high_status: int = 0
    pump_b1_low_status: int = 0
    pump_b2_high_status: int = 0
    pump_b2_low_status: int = 0
    lead_pump: int = 0


class PumpSimulator:
    """Simulator for pump lead-lag control.

    Implements:
    - Level-based pump control with hysteresis
    - Lead-lag rotation for runtime equalization
    - High/low speed staging
    """

    def __init__(self, cfg: dict[str, Any], rng: np.random.Generator):
        """Initialize pump simulator.

        Args:
            cfg: Pump configuration
            rng: NumPy random generator
        """
        self.cfg = cfg
        self.rng = rng

        ctrl_cfg = cfg.get("control", {})

        # Level thresholds
        self.level_high_on = float(ctrl_cfg.get("level_high_on_percent", 48))
        self.level_low_off = float(ctrl_cfg.get("level_low_off_percent", 42))

        # Timing
        self.min_on_minutes = float(ctrl_cfg.get("min_on_minutes", 20))
        self.min_off_minutes = float(ctrl_cfg.get("min_off_minutes", 20))
        rotation_hours = float(ctrl_cfg.get("lead_lag_rotation_hours", 48))

        # Lead-lag controller
        self.lead_lag = LeadLagController(n_units=2, rotation_hours=rotation_hours)

        # Per-pump timers
        self._timers = {
            "b1": MinOnOffTimer(self.min_on_minutes, self.min_off_minutes, state=False),
            "b2": MinOnOffTimer(self.min_on_minutes, self.min_off_minutes, state=False),
        }

        # Track pump running state
        self._pump_running = {"b1": False, "b2": False}

    def init_state(self) -> PumpState:
        """Initialize pump state."""
        return PumpState(
            pump_b1_high_status=0,
            pump_b1_low_status=0,
            pump_b2_high_status=0,
            pump_b2_low_status=0,
            lead_pump=0,
        )

    def step(
        self,
        state: PumpState,
        dt_minutes: float,
        separator_level: float
    ) -> PumpState:
        """Advance pump simulation by one timestep.

        Args:
            state: Current pump state
            dt_minutes: Time step in minutes
            separator_level: Current separator level (%)

        Returns:
            Updated pump state
        """
        # Update timers
        for timer in self._timers.values():
            timer.update_time(dt_minutes)

        # Determine pump demand based on level
        # High level -> need to pump down
        # Low level -> can reduce pumping
        n_pumps_needed = 0

        if separator_level > self.level_high_on:
            n_pumps_needed = 2  # Both pumps needed
        elif separator_level > (self.level_high_on + self.level_low_off) / 2:
            n_pumps_needed = 1  # One pump sufficient
        elif separator_level < self.level_low_off:
            n_pumps_needed = 0  # Can turn off

        # Use lead-lag to select which pumps
        selected = self.lead_lag.select_units(n_pumps_needed)

        # Apply timing constraints
        b1_desired = 0 in selected
        b2_desired = 1 in selected

        b1_actual = self._timers["b1"].change_state(b1_desired)
        b2_actual = self._timers["b2"].change_state(b2_desired)

        # Update lead-lag runtimes
        self.lead_lag.update([b1_actual, b2_actual], dt_minutes / 60)

        # Determine high/low speed based on level urgency
        high_speed = separator_level > (self.level_high_on + 10)

        # Set output states
        b1_high = 1 if (b1_actual and high_speed) else 0
        b1_low = 1 if (b1_actual and not high_speed) else 0
        b2_high = 1 if (b2_actual and high_speed) else 0
        b2_low = 1 if (b2_actual and not high_speed) else 0

        return PumpState(
            pump_b1_high_status=b1_high,
            pump_b1_low_status=b1_low,
            pump_b2_high_status=b2_high,
            pump_b2_low_status=b2_low,
            lead_pump=self.lead_lag.lead_index,
        )

    def is_pump_running(self, state: PumpState, pump_id: str) -> bool:
        """Check if a pump is running (any speed)."""
        if pump_id == "b1":
            return state.pump_b1_high_status == 1 or state.pump_b1_low_status == 1
        elif pump_id == "b2":
            return state.pump_b2_high_status == 1 or state.pump_b2_low_status == 1
        return False

    def calculate_power(self, state: PumpState, power_per_pump_kw: float = 1.2) -> float:
        """Calculate total pump power consumption (kW)."""
        power = 0.0
        if state.pump_b1_high_status:
            power += power_per_pump_kw * 1.2  # High speed uses more power
        elif state.pump_b1_low_status:
            power += power_per_pump_kw * 0.6

        if state.pump_b2_high_status:
            power += power_per_pump_kw * 1.2
        elif state.pump_b2_low_status:
            power += power_per_pump_kw * 0.6

        return power
