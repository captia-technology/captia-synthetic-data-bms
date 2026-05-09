"""Energy metering model for Industrial Refrigeration.

Implements power, energy, and power quality calculations.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np


@dataclass
class EnergyState:
    """State of the energy metering system.

    Attributes:
        power_active_total: Total active power (kW)
        power_apparent_total: Total apparent power (kVA)
        power_factor: Power factor
        energy_active: Cumulative active energy (kWh)
        power_active_phase_a: Phase A active power (kW)
        power_active_phase_b: Phase B active power (kW)
        power_active_phase_c: Phase C active power (kW)
    """
    power_active_total: float = 50.0
    power_apparent_total: float = 60.0
    power_factor: float = 0.83
    energy_active: float = 0.0
    power_active_phase_a: float = 16.0
    power_active_phase_b: float = 17.0
    power_active_phase_c: float = 17.0


class EnergyMeterSimulator:
    """Simulator for energy metering and power quality.

    Implements:
    - Total power aggregation from all sources
    - Power factor modeling
    - Three-phase power distribution
    - Cumulative energy integration (monotonic)
    """

    def __init__(self, cfg: dict[str, Any], rng: np.random.Generator):
        """Initialize energy meter simulator.

        Args:
            cfg: Energy model configuration
            rng: NumPy random generator
        """
        self.cfg = cfg
        self.rng = rng

        model_cfg = cfg.get("model", {})
        self.base_load_kw = float(model_cfg.get("base_load_kW", 5.0))
        self.phase_imbalance_sigma = float(model_cfg.get("phase_imbalance_sigma", 0.06))

        pf_cfg = model_cfg.get("pf_model", {})
        self.pf_base = float(pf_cfg.get("base", 0.72))
        self.pf_load_gain = float(pf_cfg.get("load_gain", 0.18))
        self.pf_clamp = tuple(pf_cfg.get("clamp", [0.4, 1.0]))

        # Condenser power model coefficients
        cond_cfg = model_cfg.get("condenser_power_from_vfd", {})
        self.cond_a = float(cond_cfg.get("a", 0.8))
        self.cond_b = float(cond_cfg.get("b", 0.06))
        self.cond_c = float(cond_cfg.get("c", 0.002))

        self.pump_power_kw = float(model_cfg.get("pump_power_kW_each", 1.2))

    def init_state(self) -> EnergyState:
        """Initialize energy state."""
        return EnergyState(
            power_active_total=self.base_load_kw,
            power_apparent_total=self.base_load_kw / 0.8,
            power_factor=0.8,
            energy_active=0.0,
            power_active_phase_a=self.base_load_kw / 3,
            power_active_phase_b=self.base_load_kw / 3,
            power_active_phase_c=self.base_load_kw / 3,
        )

    def step(
        self,
        state: EnergyState,
        dt_minutes: float,
        compressor_power_kw: float,
        condenser_vfd_hz: float,
        pump_power_kw: float
    ) -> EnergyState:
        """Advance energy simulation by one timestep.

        Args:
            state: Current energy state
            dt_minutes: Time step in minutes
            compressor_power_kw: Total compressor power
            condenser_vfd_hz: Condenser VFD frequency
            pump_power_kw: Total pump power

        Returns:
            Updated energy state
        """
        # Calculate condenser power
        f = condenser_vfd_hz
        condenser_power = self.cond_a + self.cond_b * f + self.cond_c * f * f

        # Total active power
        total_power = (
            self.base_load_kw
            + compressor_power_kw
            + condenser_power
            + pump_power_kw
        )

        # Add small noise
        total_power += self.rng.normal(0, total_power * 0.01)
        total_power = max(0, total_power)

        # Power factor model
        # PF improves with load (motors more efficient at higher load)
        load_fraction = min(1.0, total_power / 300)  # Assume 300 kW full load
        pf = self.pf_base + self.pf_load_gain * load_fraction
        pf += self.rng.normal(0, 0.01)
        pf = float(np.clip(pf, *self.pf_clamp))

        # Apparent power
        apparent_power = total_power / max(0.1, pf)

        # Phase distribution with imbalance
        # Should sum to approximately total_power
        imbalance_a = 1 + self.rng.normal(0, self.phase_imbalance_sigma)
        imbalance_b = 1 + self.rng.normal(0, self.phase_imbalance_sigma)
        imbalance_c = 1 + self.rng.normal(0, self.phase_imbalance_sigma)

        # Normalize so they sum correctly
        total_imbalance = imbalance_a + imbalance_b + imbalance_c
        phase_a = total_power * (imbalance_a / total_imbalance)
        phase_b = total_power * (imbalance_b / total_imbalance)
        phase_c = total_power * (imbalance_c / total_imbalance)

        # Energy integration (monotonically increasing)
        dt_hours = dt_minutes / 60
        energy_increment = total_power * dt_hours
        new_energy = state.energy_active + energy_increment

        return EnergyState(
            power_active_total=round(total_power, 2),
            power_apparent_total=round(apparent_power, 2),
            power_factor=round(pf, 3),
            energy_active=round(new_energy, 3),
            power_active_phase_a=round(phase_a, 2),
            power_active_phase_b=round(phase_b, 2),
            power_active_phase_c=round(phase_c, 2),
        )
