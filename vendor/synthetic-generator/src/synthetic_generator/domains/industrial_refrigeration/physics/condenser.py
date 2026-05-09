"""Condenser model for Industrial Refrigeration.

Implements VFD PI control for discharge pressure regulation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from ....core.control_utils import PIController


@dataclass
class CondenserState:
    """State of the condenser system.

    Attributes:
        condenser_discharge_pressure: Discharge pressure at condenser (bar)
        condenser_discharge_temperature: Discharge temperature (°C)
        condenser_vfd_frequency: VFD frequency (Hz)
        effectiveness: Condenser effectiveness (0-1)
    """
    condenser_discharge_pressure: float = 18.0
    condenser_discharge_temperature: float = 40.0
    condenser_vfd_frequency: float = 35.0
    effectiveness: float = 0.7


class CondenserSimulator:
    """Simulator for condenser dynamics with VFD control.

    Implements:
    - PI control for VFD frequency based on discharge pressure
    - Effectiveness model based on VFD frequency
    - Temperature correlation with pressure and ambient
    """

    def __init__(self, cfg: dict[str, Any], rng: np.random.Generator):
        """Initialize condenser simulator.

        Args:
            cfg: Condenser configuration
            rng: NumPy random generator
        """
        self.cfg = cfg
        self.rng = rng

        ctrl_cfg = cfg.get("control", {})

        # VFD limits
        vfd_limits = ctrl_cfg.get("vfd_frequency_limits_hz", [0, 50])
        self.vfd_min = float(vfd_limits[0])
        self.vfd_max = float(vfd_limits[1])

        # PI controller parameters
        pi_cfg = ctrl_cfg.get("pi", {})
        sp_cfg = pi_cfg.get("discharge_pressure_setpoint_bar", {})
        self.sp_base = float(sp_cfg.get("base", 24.0))
        self.sp_ambient_gain = float(sp_cfg.get("ambient_gain", 0.20))
        self.sp_clamp = tuple(sp_cfg.get("clamp", [16, 34]))

        kp = float(pi_cfg.get("kp", 1.4))
        ki = float(pi_cfg.get("ki", 0.08))
        integrator_clamp = pi_cfg.get("integrator_clamp", [-200, 200])

        self.pi = PIController(
            setpoint=self.sp_base,
            kp=kp,
            ki=ki,
            output_min=self.vfd_min,
            output_max=self.vfd_max,
            integrator_min=float(integrator_clamp[0]),
            integrator_max=float(integrator_clamp[1]),
        )

        # Response lag
        self.response_lag_minutes = float(ctrl_cfg.get("response_lag_minutes", 10))

        # Effectiveness model
        eff_cfg = ctrl_cfg.get("effectiveness_from_vfd", {})
        self.eff_gain = float(eff_cfg.get("gain", 0.9))

    def init_state(self) -> CondenserState:
        """Initialize condenser state."""
        return CondenserState(
            condenser_discharge_pressure=18.0 + self.rng.normal(0, 0.5),
            condenser_discharge_temperature=40.0 + self.rng.normal(0, 2),
            condenser_vfd_frequency=35.0 + self.rng.normal(0, 2),
            effectiveness=0.7,
        )

    def step(
        self,
        state: CondenserState,
        dt_minutes: float,
        rack_discharge_pressure: float,
        ambient_temp: float
    ) -> CondenserState:
        """Advance condenser simulation by one timestep.

        Args:
            state: Current condenser state
            dt_minutes: Time step in minutes
            rack_discharge_pressure: Discharge pressure from rack
            ambient_temp: Ambient temperature

        Returns:
            Updated condenser state
        """
        # Calculate dynamic setpoint based on ambient
        setpoint = self.sp_base + self.sp_ambient_gain * ambient_temp
        setpoint = float(np.clip(setpoint, *self.sp_clamp))
        self.pi.setpoint = setpoint

        # PI control for VFD frequency
        # Note: Higher pressure error -> higher frequency needed
        new_vfd = self.pi.update(rack_discharge_pressure, dt_minutes)

        # Apply lag (first-order filter)
        alpha = dt_minutes / self.response_lag_minutes
        alpha = min(alpha, 1.0)
        filtered_vfd = state.condenser_vfd_frequency + alpha * (new_vfd - state.condenser_vfd_frequency)
        filtered_vfd = float(np.clip(filtered_vfd, self.vfd_min, self.vfd_max))

        # Calculate effectiveness (quadratic relationship with frequency)
        # Higher frequency = more airflow = better heat rejection
        normalized_freq = (filtered_vfd - self.vfd_min) / (self.vfd_max - self.vfd_min)
        effectiveness = self.eff_gain * (normalized_freq ** 0.5)  # sqrt for diminishing returns
        effectiveness = float(np.clip(effectiveness + self.rng.normal(0, 0.02), 0.1, 1.0))

        # Condenser discharge pressure follows rack with some damping
        new_pressure = 0.9 * rack_discharge_pressure + 0.1 * state.condenser_discharge_pressure
        new_pressure += self.rng.normal(0, 0.1)
        new_pressure = float(np.clip(new_pressure, 5, 40))

        # Discharge temperature
        new_temp = ambient_temp + 10 + 0.3 * (new_pressure - 15)
        new_temp += self.rng.normal(0, 0.5)
        new_temp = float(np.clip(new_temp, -10, 60))

        return CondenserState(
            condenser_discharge_pressure=new_pressure,
            condenser_discharge_temperature=new_temp,
            condenser_vfd_frequency=filtered_vfd,
            effectiveness=effectiveness,
        )

    def calculate_power(self, state: CondenserState) -> float:
        """Calculate condenser fan power consumption (kW).

        Power is approximately quadratic with frequency.
        """
        cfg = self.cfg.get("control", {}).get("effectiveness_from_vfd", {})
        # P = a + b*f + c*f^2
        # Default model for typical industrial condenser fans
        a = 0.8
        b = 0.06
        c = 0.002
        f = state.condenser_vfd_frequency
        return a + b * f + c * f * f
