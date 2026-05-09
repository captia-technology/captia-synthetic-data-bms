"""Cold chamber thermal model for Industrial Refrigeration.

Implements first-order thermal dynamics with evaporator control and defrost cycles.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import numpy as np

from ....core.control_utils import HysteresisController, MinOnOffTimer


@dataclass
class ChamberState:
    """State of a cold chamber.

    Attributes:
        chamber_id: Chamber identifier
        temperature: Current temperature (°C)
        setpoint: Temperature setpoint (°C)
        evap1_cooling_cmd: Evaporator 1 cooling command (0/1)
        evap1_defrost_cmd: Evaporator 1 defrost command (0/1)
        evap2_cooling_cmd: Evaporator 2 cooling command (0/1)
        evap2_defrost_cmd: Evaporator 2 defrost command (0/1)
        thermal_capacity: Thermal capacity (kJ/°C)
        ua_value: Heat transfer coefficient (kW/°C)
        time_since_defrost: Minutes since last defrost
        defrost_interval: Minutes between defrost cycles
        in_defrost: Whether currently in defrost cycle
        defrost_remaining: Minutes remaining in defrost
    """
    chamber_id: str
    temperature: float = -20.0
    setpoint: float = -20.0
    evap1_cooling_cmd: int = 0
    evap1_defrost_cmd: int = 0
    evap2_cooling_cmd: int = 0
    evap2_defrost_cmd: int = 0
    thermal_capacity: float = 2500.0  # kJ/°C
    ua_value: float = 0.35  # kW/°C
    time_since_defrost: float = 0.0
    defrost_interval: float = 480.0  # 8 hours
    in_defrost: bool = False
    defrost_remaining: float = 0.0


class ChamberSimulator:
    """Simulator for cold chamber thermal dynamics.

    Implements:
    - First-order thermal model
    - Hysteresis control for evaporators
    - Defrost cycles
    - Door opening events (heat pulses)
    """

    def __init__(self, cfg: dict[str, Any], rng: np.random.Generator):
        """Initialize chamber simulator.

        Args:
            cfg: Chamber physics configuration
            rng: NumPy random generator
        """
        self.cfg = cfg
        self.rng = rng

        # Control parameters
        ctrl_cfg = cfg.get("control", {})
        deadband = ctrl_cfg.get("setpoint_deadband_C", {})
        self.deadband_high = float(deadband.get("high", 0.6))
        self.deadband_low = float(deadband.get("low", 0.4))
        self.min_on_minutes = float(ctrl_cfg.get("min_on_minutes", 10))
        self.min_off_minutes = float(ctrl_cfg.get("min_off_minutes", 10))
        self.evap2_error_threshold = float(
            ctrl_cfg.get("evap2_enable_rule", {}).get("enable_if_error_C_greater_than", 1.8)
        )

        # Defrost parameters
        defrost_cfg = ctrl_cfg.get("defrost", {})
        self.defrost_enabled = defrost_cfg.get("enabled", True)
        self.defrost_duration_mean = float(
            defrost_cfg.get("duration_minutes", {}).get("mean", 25)
        )
        self.recovery_lockout = float(defrost_cfg.get("recovery_lockout_minutes", 10))

        # Thermal model parameters
        thermal_cfg = cfg.get("thermal_model", {})
        self.cth_mean = float(thermal_cfg.get("Cth_kJ_per_C", {}).get("mean", 2500))
        self.cth_sigma = float(thermal_cfg.get("Cth_kJ_per_C", {}).get("sigma", 0.35))
        self.ua_mean = float(thermal_cfg.get("UA_kW_per_C", {}).get("mean", 0.35))
        self.ua_sigma = float(thermal_cfg.get("UA_kW_per_C", {}).get("sigma", 0.40))

        # Door event parameters
        door_cfg = thermal_cfg.get("door_event_rate_per_hour", {}).get("profile", {})
        self.door_rates = {
            "night": door_cfg.get("night", 0.02),
            "morning": door_cfg.get("morning", 0.08),
            "afternoon": door_cfg.get("afternoon", 0.10),
            "evening": door_cfg.get("evening", 0.04),
        }
        self.door_heat_mean = float(
            thermal_cfg.get("door_event_heat_pulse_kW", {}).get("mean", 8.0)
        )

        # Per-chamber controllers (created on init_chamber)
        self._controllers: dict[str, HysteresisController] = {}
        self._timers: dict[str, MinOnOffTimer] = {}

    def init_chamber(self, chamber_id: str, setpoint: float = -20.0) -> ChamberState:
        """Initialize a new chamber state.

        Args:
            chamber_id: Chamber identifier
            setpoint: Temperature setpoint

        Returns:
            Initial chamber state
        """
        # Sample thermal parameters (lognormal distribution)
        cth = float(np.exp(self.rng.normal(np.log(self.cth_mean), self.cth_sigma)))
        ua = float(np.exp(self.rng.normal(np.log(self.ua_mean), self.ua_sigma)))

        # Sample defrost interval
        defrost_choices = [360, 480, 720]  # 6, 8, 12 hours
        defrost_interval = float(self.rng.choice(defrost_choices))

        # Initialize controller
        self._controllers[chamber_id] = HysteresisController(
            setpoint=setpoint,
            deadband_high=self.deadband_high,
            deadband_low=self.deadband_low,
            state=False
        )
        self._timers[chamber_id] = MinOnOffTimer(
            min_on_minutes=self.min_on_minutes,
            min_off_minutes=self.min_off_minutes,
            state=False
        )

        # Start near setpoint with slight variation
        initial_temp = setpoint + self.rng.normal(0, 0.5)

        return ChamberState(
            chamber_id=chamber_id,
            temperature=initial_temp,
            setpoint=setpoint,
            thermal_capacity=cth,
            ua_value=ua,
            defrost_interval=defrost_interval,
            time_since_defrost=self.rng.uniform(0, defrost_interval),  # Random phase
        )

    def step(
        self,
        state: ChamberState,
        dt_minutes: float,
        ambient_temp: float,
        hour_of_day: int
    ) -> ChamberState:
        """Advance chamber simulation by one timestep.

        Args:
            state: Current chamber state
            dt_minutes: Time step in minutes
            ambient_temp: Ambient temperature (°C)
            hour_of_day: Hour of day (0-23)

        Returns:
            Updated chamber state
        """
        chamber_id = state.chamber_id

        # Get controllers
        controller = self._controllers.get(chamber_id)
        timer = self._timers.get(chamber_id)

        if controller is None or timer is None:
            # Auto-initialize if needed
            controller = HysteresisController(
                setpoint=state.setpoint,
                deadband_high=self.deadband_high,
                deadband_low=self.deadband_low,
                state=state.evap1_cooling_cmd == 1
            )
            timer = MinOnOffTimer(
                min_on_minutes=self.min_on_minutes,
                min_off_minutes=self.min_off_minutes,
                state=state.evap1_cooling_cmd == 1
            )
            self._controllers[chamber_id] = controller
            self._timers[chamber_id] = timer

        # Update controller setpoint
        controller.setpoint = state.setpoint

        # Check for defrost
        in_defrost = state.in_defrost
        defrost_remaining = state.defrost_remaining
        time_since_defrost = state.time_since_defrost

        if in_defrost:
            # Continue defrost
            defrost_remaining -= dt_minutes
            if defrost_remaining <= 0:
                in_defrost = False
                defrost_remaining = 0
                time_since_defrost = 0
        else:
            time_since_defrost += dt_minutes
            # Check if defrost needed
            if self.defrost_enabled and time_since_defrost >= state.defrost_interval:
                in_defrost = True
                defrost_remaining = max(10, self.rng.normal(self.defrost_duration_mean, 8))

        # Calculate heat loads
        q_load = self._calculate_heat_load(state, ambient_temp, hour_of_day, dt_minutes)
        q_defrost = self._calculate_defrost_heat(in_defrost, dt_minutes)

        # Control logic (disabled during defrost + recovery)
        evap1_cmd = 0
        evap2_cmd = 0
        if not in_defrost and time_since_defrost >= self.recovery_lockout:
            # Hysteresis control for evap1
            desired = controller.update(state.temperature)
            timer.update_time(dt_minutes)
            actual = timer.change_state(desired)
            evap1_cmd = 1 if actual else 0

            # Evap2 for large errors
            error = state.temperature - state.setpoint
            if error > self.evap2_error_threshold and evap1_cmd == 1:
                evap2_cmd = 1

        # Calculate cooling power
        q_cool = self._calculate_cooling_power(evap1_cmd, evap2_cmd, state.setpoint)

        # Thermal dynamics: T[t+1] = T[t] + (dt/C_th)*(Q_load + Q_defrost - Q_cool) + noise
        dt_sec = dt_minutes * 60
        c_th_kj = state.thermal_capacity
        dT = (dt_sec / 1000 / c_th_kj) * (q_load + q_defrost - q_cool)
        noise = self.rng.normal(0, 0.08)
        new_temp = state.temperature + dT + noise

        # Clamp to reasonable range
        new_temp = float(np.clip(new_temp, -40, 30))

        return ChamberState(
            chamber_id=chamber_id,
            temperature=new_temp,
            setpoint=state.setpoint,
            evap1_cooling_cmd=evap1_cmd,
            evap1_defrost_cmd=1 if in_defrost else 0,
            evap2_cooling_cmd=evap2_cmd,
            evap2_defrost_cmd=1 if in_defrost else 0,
            thermal_capacity=state.thermal_capacity,
            ua_value=state.ua_value,
            time_since_defrost=time_since_defrost,
            defrost_interval=state.defrost_interval,
            in_defrost=in_defrost,
            defrost_remaining=defrost_remaining,
        )

    def _calculate_heat_load(
        self,
        state: ChamberState,
        ambient_temp: float,
        hour_of_day: int,
        dt_minutes: float
    ) -> float:
        """Calculate heat load from ambient and door events (kW)."""
        # Ambient heat transfer
        q_ambient = state.ua_value * (ambient_temp - state.temperature)

        # Door events (Poisson process with time-of-day profile)
        if 0 <= hour_of_day < 6:
            rate = self.door_rates["night"]
        elif 6 <= hour_of_day < 12:
            rate = self.door_rates["morning"]
        elif 12 <= hour_of_day < 18:
            rate = self.door_rates["afternoon"]
        else:
            rate = self.door_rates["evening"]

        # Probability of door event this timestep
        p_door = rate * dt_minutes / 60
        q_door = 0.0
        if self.rng.random() < p_door:
            q_door = self.rng.lognormal(np.log(self.door_heat_mean), 0.6)

        return q_ambient + q_door

    def _calculate_defrost_heat(self, in_defrost: bool, dt_minutes: float) -> float:
        """Calculate defrost heat input (kW)."""
        if not in_defrost:
            return 0.0
        # Defrost heater ~2-5 kW
        return self.rng.uniform(2.0, 5.0)

    def _calculate_cooling_power(
        self,
        evap1_cmd: int,
        evap2_cmd: int,
        setpoint: float
    ) -> float:
        """Calculate cooling power from evaporators (kW)."""
        # Base cooling power depends on setpoint (colder = more power needed)
        base_power = 3.0 + 0.1 * abs(setpoint)

        q_cool = 0.0
        if evap1_cmd:
            q_cool += base_power * self.rng.uniform(0.9, 1.1)
        if evap2_cmd:
            q_cool += base_power * 0.8 * self.rng.uniform(0.9, 1.1)

        return q_cool
