"""Energy simulation for discrete manufacturing.

Models power consumption correlated with machine state (boolean).
"""
from __future__ import annotations

import numpy as np

from ..state import MachineState, InternalMachineState


class EnergySimulator:
    """Simulates energy consumption for machines.
    
    Key correlations:
    - machine_state=true (RUN): high power
    - machine_state=false (STOP): low/idle power
    - Startup spike on transition to RUN
    - Power integrates to energy_kwh_total
    """

    def __init__(self, physics_cfg: dict, rng: np.random.Generator):
        """Initialize energy simulator.
        
        Args:
            physics_cfg: Physics configuration dict
            rng: NumPy random generator
        """
        self.physics_cfg = physics_cfg
        self.rng = rng
        
        # Electrical config
        elec_cfg = physics_cfg.get("electrical", {})
        self.nominal_voltage = elec_cfg.get("nominal_voltage_v", 400)
        self.voltage_noise = elec_cfg.get("voltage_noise_std", 5)
        self.frequency = elec_cfg.get("frequency_hz", 50)
        
        pf_cfg = elec_cfg.get("power_factor", {})
        self.pf_idle_range = pf_cfg.get("idle_range", [0.55, 0.70])
        self.pf_run_range = pf_cfg.get("run_range", [0.78, 0.92])
        
        trans_cfg = elec_cfg.get("startup_transient", {})
        self.startup_duration = trans_cfg.get("duration_samples", 2)
        self.startup_decay = trans_cfg.get("spike_decay_rate", 0.5)

    def step(self, machine: MachineState, dt_seconds: float) -> None:
        """Execute one simulation step for energy.
        
        Args:
            machine: Current machine state
            dt_seconds: Time step in seconds
        """
        energy = machine.energy
        cfg = machine.config
        is_running = machine.di_signals.machine_state  # BOOLEAN check
        
        # Check for startup transient trigger
        was_running = machine.previous_state == InternalMachineState.RUN
        just_started = is_running and not was_running
        
        if just_started:
            energy.startup_transient_remaining = self.startup_duration
        
        # Calculate power based on state
        if machine.internal_state == InternalMachineState.OFF:
            target_power = 0.0
            energy.power_factor = 0.0
        elif machine.internal_state in [InternalMachineState.STOP_PLANNED, 
                                         InternalMachineState.MAINTENANCE]:
            target_power = cfg.idle_power_kw * 0.2
            energy.power_factor = self.rng.uniform(*self.pf_idle_range)
        elif is_running:
            load = machine.condition.load_factor
            base_power = cfg.idle_power_kw + (cfg.run_power_kw - cfg.idle_power_kw) * load
            
            if energy.startup_transient_remaining > 0:
                spike = cfg.startup_spike_factor * (energy.startup_transient_remaining / self.startup_duration)
                target_power = base_power * (1 + spike)
                energy.startup_transient_remaining -= 1
            else:
                target_power = base_power
            
            noise = self.rng.normal(0, target_power * 0.03)
            target_power = max(0, target_power + noise)
            energy.power_factor = self.rng.uniform(*self.pf_run_range)
        else:
            target_power = cfg.idle_power_kw + self.rng.normal(0, cfg.idle_power_kw * 0.05)
            target_power = max(0, target_power)
            energy.power_factor = self.rng.uniform(*self.pf_idle_range)
        
        # Smooth power transition
        alpha = 0.3
        energy.power_kw = alpha * target_power + (1 - alpha) * energy.last_power_kw
        energy.last_power_kw = energy.power_kw
        
        # Integrate energy (monotonic)
        dt_hours = dt_seconds / 3600.0
        energy.energy_kwh_total += energy.power_kw * dt_hours
        
        # Voltage with noise
        energy.voltage_v = self.nominal_voltage + self.rng.normal(0, self.voltage_noise)

    def get_current_a(self, machine: MachineState) -> float:
        """Calculate current from power, voltage and PF."""
        energy = machine.energy
        if energy.voltage_v <= 0 or energy.power_factor <= 0:
            return 0.0
        sqrt3 = np.sqrt(3)
        current = (energy.power_kw * 1000) / (sqrt3 * energy.voltage_v * energy.power_factor)
        return max(0, current)
