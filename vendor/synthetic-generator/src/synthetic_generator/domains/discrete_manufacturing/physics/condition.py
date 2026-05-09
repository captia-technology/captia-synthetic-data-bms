"""Condition monitoring for discrete manufacturing.

Models temperature, vibration, and wear correlated with machine state.
"""
from __future__ import annotations

import numpy as np

from ..state import MachineState, InternalMachineState


class ConditionSimulator:
    """Simulates condition monitoring for machines.
    
    Key correlations:
    - motor_temp_c rises with load, falls when stopped
    - vibration_rms correlates with load and wear
    - tool_wear_index grows with cycles
    - air_pressure_bar with occasional drops (pneumatic machines)
    """

    def __init__(self, physics_cfg: dict, anomaly_cfg: dict, rng: np.random.Generator):
        """Initialize condition simulator.
        
        Args:
            physics_cfg: Physics configuration dict
            anomaly_cfg: Anomaly configuration for data quality
            rng: NumPy random generator
        """
        self.physics_cfg = physics_cfg
        self.anomaly_cfg = anomaly_cfg
        self.rng = rng
        
        # Thermal config
        thermal_cfg = physics_cfg.get("thermal", {})
        self.ambient_temp = thermal_cfg.get("ambient_temp_c", 22)
        self.ambient_variation = thermal_cfg.get("ambient_temp_daily_variation", 4)
        motor_cfg = thermal_cfg.get("motor_temp", {})
        self.motor_initial = motor_cfg.get("initial_c", 25)
        self.motor_idle_eq = motor_cfg.get("idle_equilibrium_c", 32)
        self.motor_run_gain = motor_cfg.get("run_equilibrium_gain_per_load", 45)
        self.motor_max = motor_cfg.get("max_c", 95)
        self.motor_alarm = motor_cfg.get("alarm_c", 80)
        
        # Vibration config
        vib_cfg = physics_cfg.get("vibration", {})
        self.vib_noise_ratio = vib_cfg.get("noise_std_ratio", 0.12)
        self.impact_prob = vib_cfg.get("impact_probability_per_hour", 0.03)
        self.impact_mult = vib_cfg.get("impact_multiplier", 3.5)
        
        # Wear config
        wear_cfg = physics_cfg.get("wear", {})
        self.wear_rate = wear_cfg.get("degradation_rate_per_cycle", 0.00015)
        self.wear_load_gain = wear_cfg.get("load_factor_gain", 0.4)
        
        # Air pressure config
        air_cfg = physics_cfg.get("air_pressure", {})
        self.air_nominal = air_cfg.get("nominal_bar", 6.0)
        self.air_noise = air_cfg.get("noise_std", 0.15)
        self.air_low_threshold = air_cfg.get("low_threshold_bar", 5.2)
        self.air_drop_prob = air_cfg.get("drop_probability_per_hour", 0.008)
        air_drop_dur = air_cfg.get("drop_duration_minutes", {})
        self.air_drop_mean = air_drop_dur.get("mean", 3)
        self.air_drop_std = air_drop_dur.get("std", 1)

    def step(self, machine: MachineState, dt_seconds: float, hour_of_day: int) -> None:
        """Execute one simulation step for condition."""
        cfg = machine.config
        cond = machine.condition
        is_running = machine.di_signals.machine_state
        
        if is_running:
            target_load = 0.5 + 0.4 * self.rng.random()
            cond.load_factor = 0.8 * cond.load_factor + 0.2 * target_load
        else:
            cond.load_factor = max(0, cond.load_factor * 0.95)
        
        self._update_temperature(machine, dt_seconds, hour_of_day)
        self._update_vibration(machine, dt_seconds)
        if cfg.has_pneumatics:
            self._update_air_pressure(machine, dt_seconds)

    def _update_temperature(self, machine: MachineState, dt_seconds: float, hour_of_day: int) -> None:
        """Update motor temperature with first-order dynamics."""
        cfg = machine.config
        cond = machine.condition
        is_running = machine.di_signals.machine_state
        
        hour_offset = (hour_of_day - 4) % 24
        ambient = self.ambient_temp + self.ambient_variation * np.sin(2 * np.pi * hour_offset / 24)
        
        if machine.internal_state == InternalMachineState.OFF:
            target_temp = ambient
            tau_minutes = cfg.thermal_tau_minutes * 0.5
        elif is_running:
            target_temp = self.motor_idle_eq + self.motor_run_gain * cond.load_factor + (ambient - self.ambient_temp)
            tau_minutes = cfg.thermal_tau_minutes
        else:
            target_temp = self.motor_idle_eq + (ambient - self.ambient_temp)
            tau_minutes = cfg.thermal_tau_minutes * 0.7
        
        tau_seconds = tau_minutes * 60
        alpha = min(dt_seconds / tau_seconds, 0.5)
        cond.motor_temp_c += alpha * (target_temp - cond.motor_temp_c)
        cond.motor_temp_c += self.rng.normal(0, 0.3)
        cond.motor_temp_c = np.clip(cond.motor_temp_c, ambient - 5, self.motor_max)

    def _update_vibration(self, machine: MachineState, dt_seconds: float) -> None:
        """Update vibration correlated with load and wear."""
        cfg = machine.config
        cond = machine.condition
        is_running = machine.di_signals.machine_state
        
        if is_running:
            base_vib = cfg.vibration_base
            load_vib = cfg.vibration_load_gain * cond.load_factor
            wear_vib = cfg.vibration_wear_gain * cond.tool_wear_index
            target_vib = base_vib + load_vib + wear_vib
            
            p_impact = self.impact_prob * dt_seconds / 3600.0
            if self.rng.random() < p_impact:
                target_vib *= self.impact_mult
        else:
            target_vib = cfg.vibration_base * 0.1
        
        noise = self.rng.normal(0, target_vib * self.vib_noise_ratio)
        cond.vibration_rms_mm_s = max(0.01, target_vib + noise)

    def _update_air_pressure(self, machine: MachineState, dt_seconds: float) -> None:
        """Update pneumatic air pressure with occasional drops."""
        cond = machine.condition
        
        if cond.air_pressure_drop_remaining > 0:
            cond.air_pressure_drop_remaining -= 1
            cond.air_pressure_bar += 0.1
            cond.air_pressure_bar = min(cond.air_pressure_bar, self.air_nominal)
        else:
            cond.air_pressure_bar = self.air_nominal + self.rng.normal(0, self.air_noise)
            p_drop = self.air_drop_prob * dt_seconds / 3600.0
            if self.rng.random() < p_drop:
                drop_duration = max(self.air_drop_mean + self.rng.normal(0, self.air_drop_std), 1)
                cond.air_pressure_drop_remaining = int(drop_duration * 60 / dt_seconds)
                cond.air_pressure_bar = self.rng.uniform(4.5, self.air_low_threshold)
        
        cond.air_pressure_bar = np.clip(cond.air_pressure_bar, 4.0, 8.0)

    def update_wear(self, machine: MachineState, cycles_completed: int) -> None:
        """Update tool wear after cycles complete."""
        if cycles_completed <= 0:
            return
        cond = machine.condition
        wear_increment = self.wear_rate * cycles_completed * (1 + self.wear_load_gain * cond.load_factor)
        cond.tool_wear_index = min(1.0, cond.tool_wear_index + wear_increment)

    def is_air_pressure_ok(self, machine: MachineState) -> bool:
        """Check if air pressure is acceptable."""
        if not machine.config.has_pneumatics:
            return True
        return machine.condition.air_pressure_bar >= self.air_low_threshold

    def is_temp_ok(self, machine: MachineState) -> bool:
        """Check if motor temperature is below alarm."""
        return machine.condition.motor_temp_c < self.motor_alarm

    def get_scrap_rate_modifier(self, machine: MachineState) -> float:
        """Get scrap rate multiplier based on condition."""
        cond = machine.condition
        wear_factor = 1 + 2 * cond.tool_wear_index
        temp_factor = 1 + max(0, (cond.motor_temp_c - 70) / 30)
        return wear_factor * temp_factor

    def get_cycle_time_modifier(self, machine: MachineState) -> float:
        """Get cycle time multiplier based on wear."""
        return 1 + 0.15 * machine.condition.tool_wear_index
