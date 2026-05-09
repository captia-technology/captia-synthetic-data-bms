"""Compressor rack model for Industrial Refrigeration.

Implements staging control and pressure dynamics for multi-compressor systems.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from ....core.control_utils import LeadLagController, MinOnOffTimer


@dataclass
class CompressorRackState:
    """State of the compressor rack.

    Attributes:
        rack_suction_pressure: Suction pressure (bar)
        rack_discharge_pressure: Discharge pressure (bar)
        rack_suction_temperature: Suction temperature (°C)
        rack_discharge_temperature: Discharge temperature (°C)
        compressor_states: Dict of compressor_id -> on/off state
        demand: Current cooling demand (0-1 normalized)
    """
    rack_suction_pressure: float = 2.0
    rack_discharge_pressure: float = 18.0
    rack_suction_temperature: float = -25.0
    rack_discharge_temperature: float = 45.0
    compressor_states: dict[str, int] = field(default_factory=dict)
    demand: float = 0.5


class CompressorRackSimulator:
    """Simulator for compressor rack dynamics.

    Implements:
    - Staging control based on suction pressure
    - Lead-lag rotation for runtime equalization
    - Pressure dynamics (suction and discharge)
    - Temperature correlation with pressure
    """

    def __init__(self, cfg: dict[str, Any], rng: np.random.Generator):
        """Initialize compressor rack simulator.

        Args:
            cfg: Compressor rack configuration
            rng: NumPy random generator
        """
        self.cfg = cfg
        self.rng = rng

        # Compressor definitions
        self.compressor_ids = [
            "compressor_2_status",
            "compressor_3_status",
            "compressor_4_status",
            "compressor_5_status",
            "compressor_6_status",
            "compressor_8_status",
        ]
        self.n_compressors = len(self.compressor_ids)

        # Staging parameters
        staging_cfg = cfg.get("staging", {})
        self.min_on_minutes = float(staging_cfg.get("min_on_minutes", 15))
        self.min_off_minutes = float(staging_cfg.get("min_off_minutes", 15))
        rotation_hours = float(staging_cfg.get("lead_lag_rotation_hours", 72))

        # Pressure dynamics
        suction_cfg = cfg.get("suction_pressure_dynamics", {})
        self.alpha_demand = float(suction_cfg.get("alpha_demand", 0.08))
        self.beta_capacity = float(suction_cfg.get("beta_capacity", 0.12))
        self.suction_noise = float(suction_cfg.get("noise_sigma_bar", 0.03))
        self.suction_clamp = tuple(suction_cfg.get("clamp_bar", [0.2, 6.0]))

        discharge_cfg = cfg.get("discharge_pressure_dynamics", {})
        self.alpha_compression = float(discharge_cfg.get("alpha_compression", 0.10))
        self.beta_condensing = float(discharge_cfg.get("beta_condensing", 0.15))
        self.discharge_noise = float(discharge_cfg.get("noise_sigma_bar", 0.08))
        self.discharge_clamp = tuple(discharge_cfg.get("clamp_bar", [2.0, 60.0]))

        # Temperature parameters
        temp_cfg = cfg.get("temperatures", {})
        suction_temp_cfg = temp_cfg.get("suction_temp_from_pressure", {})
        self.suction_a0 = float(suction_temp_cfg.get("a0", -35.0))
        self.suction_a1 = float(suction_temp_cfg.get("a1_bar", 10.0))
        self.suction_temp_noise = float(suction_temp_cfg.get("noise_sigma_C", 0.5))

        discharge_temp_cfg = temp_cfg.get("discharge_temp", {})
        self.discharge_base_rise = float(discharge_temp_cfg.get("base_rise_C", 15))
        self.discharge_ratio_gain = float(discharge_temp_cfg.get("pressure_ratio_gain", 6.0))
        self.discharge_ambient_gain = float(discharge_temp_cfg.get("ambient_gain", 0.15))
        self.discharge_temp_noise = float(discharge_temp_cfg.get("noise_sigma_C", 0.8))

        # Power ratings
        comp_cfg = cfg.get("compressors", {})
        self.rated_power = comp_cfg.get("rated_power_kW", {
            "compressor_2_status": 35,
            "compressor_3_status": 35,
            "compressor_4_status": 40,
            "compressor_5_status": 40,
            "compressor_6_status": 45,
            "compressor_8_status": 45,
        })

        # Initialize lead-lag controller
        self.lead_lag = LeadLagController(
            n_units=self.n_compressors,
            rotation_hours=rotation_hours
        )

        # Per-compressor timers
        self._timers: dict[str, MinOnOffTimer] = {
            cid: MinOnOffTimer(self.min_on_minutes, self.min_off_minutes, state=False)
            for cid in self.compressor_ids
        }

    def init_state(self) -> CompressorRackState:
        """Initialize compressor rack state."""
        return CompressorRackState(
            rack_suction_pressure=2.0 + self.rng.normal(0, 0.1),
            rack_discharge_pressure=18.0 + self.rng.normal(0, 0.5),
            rack_suction_temperature=-25.0 + self.rng.normal(0, 1),
            rack_discharge_temperature=45.0 + self.rng.normal(0, 2),
            compressor_states={cid: 0 for cid in self.compressor_ids},
            demand=0.5,
        )

    def step(
        self,
        state: CompressorRackState,
        dt_minutes: float,
        chamber_demand: float,
        condenser_effectiveness: float,
        ambient_temp: float
    ) -> CompressorRackState:
        """Advance compressor rack simulation by one timestep.

        Args:
            state: Current rack state
            dt_minutes: Time step in minutes
            chamber_demand: Aggregate cooling demand from chambers (0-1)
            condenser_effectiveness: Condenser performance factor (0-1)
            ambient_temp: Ambient temperature for discharge temp calc

        Returns:
            Updated rack state
        """
        # Staging control based on suction pressure target
        suction_target = 2.5  # Target suction pressure
        suction_error = state.rack_suction_pressure - suction_target

        # Determine how many compressors needed
        # More compressors when suction pressure is too high (demand exceeds capacity)
        n_running = sum(state.compressor_states.values())
        n_desired = n_running

        if suction_error > 0.3:  # Pressure too high - need more capacity
            n_desired = min(n_running + 1, self.n_compressors)
        elif suction_error < -0.3:  # Pressure too low - reduce capacity
            n_desired = max(n_running - 1, 1)  # Keep at least one running

        # Apply lead-lag selection
        selected = self.lead_lag.select_units(n_desired)

        # Update compressor states with timing constraints
        new_states = {}
        for i, cid in enumerate(self.compressor_ids):
            timer = self._timers[cid]
            timer.update_time(dt_minutes)
            desired = 1 if i in selected else 0
            actual = timer.change_state(desired == 1)
            new_states[cid] = 1 if actual else 0

        # Update lead-lag runtimes
        running_list = [new_states[cid] == 1 for cid in self.compressor_ids]
        self.lead_lag.update(running_list, dt_minutes / 60)

        # Calculate capacity
        n_running_new = sum(new_states.values())
        capacity = n_running_new / self.n_compressors if self.n_compressors > 0 else 0

        # Pressure dynamics
        # Suction pressure: rises with demand, falls with capacity
        dp_suction = (
            self.alpha_demand * chamber_demand
            - self.beta_capacity * capacity
            + self.rng.normal(0, self.suction_noise)
        )
        new_suction_p = state.rack_suction_pressure + dp_suction * dt_minutes / 5
        new_suction_p = float(np.clip(new_suction_p, *self.suction_clamp))

        # Discharge pressure: rises with compression, falls with condenser
        dp_discharge = (
            self.alpha_compression * capacity
            - self.beta_condensing * condenser_effectiveness
            + self.rng.normal(0, self.discharge_noise)
        )
        new_discharge_p = state.rack_discharge_pressure + dp_discharge * dt_minutes / 5
        new_discharge_p = float(np.clip(new_discharge_p, *self.discharge_clamp))

        # Temperature calculations
        # Suction temp correlates with suction pressure
        new_suction_t = (
            self.suction_a0 + self.suction_a1 * new_suction_p
            + self.rng.normal(0, self.suction_temp_noise)
        )
        new_suction_t = float(np.clip(new_suction_t, -60, 30))

        # Discharge temp depends on pressure ratio and ambient
        pressure_ratio = new_discharge_p / max(0.5, new_suction_p)
        new_discharge_t = (
            new_suction_t + self.discharge_base_rise
            + self.discharge_ratio_gain * np.log(pressure_ratio)
            + self.discharge_ambient_gain * ambient_temp
            + self.rng.normal(0, self.discharge_temp_noise)
        )
        new_discharge_t = float(np.clip(new_discharge_t, -40, 120))

        return CompressorRackState(
            rack_suction_pressure=new_suction_p,
            rack_discharge_pressure=new_discharge_p,
            rack_suction_temperature=new_suction_t,
            rack_discharge_temperature=new_discharge_t,
            compressor_states=new_states,
            demand=chamber_demand,
        )

    def calculate_power(self, state: CompressorRackState) -> float:
        """Calculate total compressor power consumption (kW)."""
        total_power = 0.0
        for cid, running in state.compressor_states.items():
            if running:
                rated = self.rated_power.get(cid, 40)
                # Part load factor varies
                plf = self.rng.uniform(0.55, 1.05)
                total_power += rated * plf

        return total_power
