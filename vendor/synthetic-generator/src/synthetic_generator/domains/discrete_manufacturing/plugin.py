"""Discrete Manufacturing domain plugin.

Main plugin class that implements the DomainPlugin interface
for manufacturing plant simulation.

CRITICAL DESIGN DECISIONS:
1. machine_state is BOOLEAN (true=RUN, false=STOP), NOT string
2. All 6DI signals are BOOLEAN (WISE digital inputs model)
3. Support for pieces_per_cycle (e.g., welding robot with 11)
4. Physics-correlated signals (power/temp/vibration vs state)
5. NO KPIs calculated - only raw primary signals
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Iterator, Optional

import numpy as np
import pandas as pd

from ..base import DomainPlugin
from ..registry import register_domain
from ...core.models import (
    Inventory,
    DataPoint,
    DataType,
    PointType,
    Quality,
)
from ...core.pv import build_pvn


from .inventory import build_manufacturing_inventory
from .context import build_manufacturing_context, ManufacturingContext
from .state import MachineState, InternalMachineState
from .physics.machine import MachineStateMachine, TransitionContext
from .physics.energy import EnergySimulator
from .physics.condition import ConditionSimulator
from .physics.production import ProductionSimulator

LOG = logging.getLogger("synthetic_generator.domains.discrete_manufacturing")


@register_domain
class DiscreteManufacturingPlugin(DomainPlugin):
    """Domain plugin for Discrete Manufacturing.
    
    Generates synthetic OT telemetry data for manufacturing plants:
    - Configurable machines with WISE 6DI boolean signals
    - machine_state as BOOLEAN (true=RUN, false=STOP)
    - Production cycles with pieces_per_cycle support
    - Energy consumption correlated with state
    - Condition monitoring (temp, vibration, wear)
    - Configurable shift calendar
    
    All signals are raw primary data - NO KPIs calculated.
    """

    @property
    def domain_id(self) -> str:
        return "discrete_manufacturing"

    @property
    def description(self) -> str:
        return "Discrete manufacturing plant with WISE 6DI boolean signals"

    @property
    def version(self) -> str:
        return "1.0.0"

    def build_inventory(
        self,
        project_cfg: dict[str, Any],
        domain_cfg: dict[str, Any]
    ) -> Inventory:
        """Build manufacturing inventory from configuration."""
        simulation = project_cfg.get("simulation", {})
        seed = simulation.get("seed", 42)
        rng = np.random.default_rng(seed)
        
        inventory, _ = build_manufacturing_inventory(project_cfg, domain_cfg, rng)
        return inventory

    def build_context(
        self,
        time_index: pd.DatetimeIndex,
        project_cfg: dict[str, Any],
        domain_cfg: dict[str, Any],
        rng: np.random.Generator
    ) -> ManufacturingContext:
        """Build simulation context with plant state and schedulers."""
        inventory, machine_configs = build_manufacturing_inventory(project_cfg, domain_cfg, rng)
        
        return build_manufacturing_context(
            time_index, project_cfg, domain_cfg, machine_configs, rng
        )

    def simulate(
        self,
        time_index: pd.DatetimeIndex,
        inventory: Inventory,
        ctx: ManufacturingContext,
        rng: np.random.Generator
    ) -> Iterator[DataPoint]:
        """Generate simulated data points for the manufacturing plant.
        
        Args:
            time_index: Time points for simulation
            inventory: Plant inventory
            ctx: Simulation context
            rng: NumPy random generator
            
        Yields:
            DataPoint objects for each measurement
        """
        site_id = inventory.metadata.get("site_id", "PLANT_001")
        dt_minutes = float((time_index[1] - time_index[0]).total_seconds() / 60)
        dt_seconds = dt_minutes * 60
        
        # Initialize simulators
        state_machine = MachineStateMachine(ctx.physics_cfg, ctx.anomaly_cfg, rng)
        energy_sim = EnergySimulator(ctx.physics_cfg, rng)
        condition_sim = ConditionSimulator(ctx.physics_cfg, ctx.anomaly_cfg, rng)
        production_sim = ProductionSimulator(ctx.physics_cfg, ctx.product_catalog, rng)
        
        machine_ids = list(ctx.plant_state.machines.keys())
        LOG.info("Simulating %d machines over %d timesteps", len(machine_ids), len(time_index))
        
        for i, ts in enumerate(time_index):
            timestamp = ts.to_pydatetime()
            ctx.plant_state.current_time = timestamp
            hour_of_day = ts.hour
            
            ctx.plant_state.shift_active = ctx.scheduler.is_shift_active(timestamp)
            ctx.plant_state.break_active = ctx.scheduler.is_break_active(timestamp)
            
            for machine_id in machine_ids:
                machine = ctx.plant_state.machines[machine_id]
                
                operator_present = ctx.scheduler.is_operator_present(timestamp, machine_id)
                
                current_order = ctx.scheduler.orders.get(machine_id)
                order = ctx.scheduler.get_or_create_order(machine_id, timestamp, current_order)
                
                has_order = order is not None and order.status == "ACTIVE"
                
                if has_order and order.order_id != machine.order_id:
                    if ctx.scheduler.needs_setup(machine_id, order, machine.product_id):
                        state_machine.trigger_setup(machine, order.product_id, order.order_id)
                    else:
                        machine.order_id = order.order_id
                        machine.product_id = order.product_id
                
                air_ok = condition_sim.is_air_pressure_ok(machine)
                temp_ok = condition_sim.is_temp_ok(machine)
                material_present = machine.di_signals.material_present
                
                trans_ctx = TransitionContext(
                    dt_seconds=dt_seconds,
                    shift_active=ctx.plant_state.shift_active,
                    break_active=ctx.plant_state.break_active,
                    has_order=has_order,
                    operator_present=operator_present,
                    air_pressure_ok=air_ok,
                    temp_ok=temp_ok,
                    material_present=material_present,
                )
                
                state_machine.step(machine, trans_ctx)
                condition_sim.step(machine, dt_seconds, hour_of_day)
                energy_sim.step(machine, dt_seconds)
                
                scrap_mod = condition_sim.get_scrap_rate_modifier(machine)
                ct_mod = condition_sim.get_cycle_time_modifier(machine)
                cycles_completed = production_sim.step(machine, dt_seconds, scrap_mod, ct_mod)
                
                condition_sim.update_wear(machine, cycles_completed)
                self._apply_anomalies(machine, ctx.anomaly_cfg, rng)
                
                if has_order:
                    ctx.scheduler.update_order_quantity(machine_id, machine.counters.good_count_total)
                
                yield from self._yield_machine_points(timestamp, site_id, machine, energy_sim)
            
            if i > 0 and i % 10000 == 0:
                LOG.info("Processed %d/%d timesteps", i, len(time_index))

    def _apply_anomalies(self, machine: MachineState, anomaly_cfg: dict, rng: np.random.Generator) -> None:
        """Apply data quality anomalies to machine signals."""
        p_missing = anomaly_cfg.get("p_missing", 0.0015)
        p_outlier = anomaly_cfg.get("p_outlier", 0.0004)
        p_stuck = anomaly_cfg.get("p_stuck", 0.0002)
        
        rand = rng.random()
        if rand < p_missing:
            machine.data_quality = "MISSING"
        elif rand < p_missing + p_outlier:
            machine.data_quality = "OUTLIER"
        elif rand < p_missing + p_outlier + p_stuck:
            machine.data_quality = "STUCK"
        else:
            machine.data_quality = "OK"

    def _yield_machine_points(
        self,
        timestamp,
        site_id: str,
        machine: MachineState,
        energy_sim: EnergySimulator
    ) -> Iterator[DataPoint]:
        """Yield all data points for a machine at one timestep.
        
        CRITICAL: machine_state and all DI signals are BOOLEAN.
        """
        machine_id = machine.machine_id
        
        # === A) WISE 6DI Digital Inputs - ALL BOOLEANS ===
        yield DataPoint(
            timestamp=timestamp, domain_id=self.domain_id, site_id=site_id,
            asset_id=machine_id, variable="machine_state",
            value=machine.di_signals.machine_state, unit="",
            data_type=DataType.BOOLEAN, point_type=PointType.SENSOR,
            pvn=build_pvn(machine_id, "machine_state"),
        )
        
        yield DataPoint(
            timestamp=timestamp, domain_id=self.domain_id, site_id=site_id,
            asset_id=machine_id, variable="fault_active",
            value=machine.di_signals.fault_active, unit="",
            data_type=DataType.BOOLEAN, point_type=PointType.SENSOR,
            pvn=build_pvn(machine_id, "fault_active"),
        )
        
        yield DataPoint(
            timestamp=timestamp, domain_id=self.domain_id, site_id=site_id,
            asset_id=machine_id, variable="estop_active",
            value=machine.di_signals.estop_active, unit="",
            data_type=DataType.BOOLEAN, point_type=PointType.SENSOR,
            pvn=build_pvn(machine_id, "estop_active"),
        )
        
        yield DataPoint(
            timestamp=timestamp, domain_id=self.domain_id, site_id=site_id,
            asset_id=machine_id, variable="cycle_in_progress",
            value=machine.di_signals.cycle_in_progress, unit="",
            data_type=DataType.BOOLEAN, point_type=PointType.SENSOR,
            pvn=build_pvn(machine_id, "cycle_in_progress"),
        )
        
        yield DataPoint(
            timestamp=timestamp, domain_id=self.domain_id, site_id=site_id,
            asset_id=machine_id, variable="material_present",
            value=machine.di_signals.material_present, unit="",
            data_type=DataType.BOOLEAN, point_type=PointType.SENSOR,
            pvn=build_pvn(machine_id, "material_present"),
        )
        
        yield DataPoint(
            timestamp=timestamp, domain_id=self.domain_id, site_id=site_id,
            asset_id=machine_id, variable="operator_present",
            value=machine.di_signals.operator_present, unit="",
            data_type=DataType.BOOLEAN, point_type=PointType.SENSOR,
            pvn=build_pvn(machine_id, "operator_present"),
        )
        
        yield DataPoint(
            timestamp=timestamp, domain_id=self.domain_id, site_id=site_id,
            asset_id=machine_id, variable="setup_active",
            value=machine.di_signals.setup_active, unit="",
            data_type=DataType.BOOLEAN, point_type=PointType.SENSOR,
            pvn=build_pvn(machine_id, "setup_active"),
        )
        
        # === B) Production signals ===
        yield DataPoint(
            timestamp=timestamp, domain_id=self.domain_id, site_id=site_id,
            asset_id=machine_id, variable="cycle_count_total",
            value=machine.counters.cycle_count_total, unit="cycles",
            data_type=DataType.INTEGER, point_type=PointType.SENSOR,
            pvn=build_pvn(machine_id, "cycle_count_total"),
        )
        
        yield DataPoint(
            timestamp=timestamp, domain_id=self.domain_id, site_id=site_id,
            asset_id=machine_id, variable="good_count_total",
            value=machine.counters.good_count_total, unit="pcs",
            data_type=DataType.INTEGER, point_type=PointType.SENSOR,
            pvn=build_pvn(machine_id, "good_count_total"),
        )
        
        yield DataPoint(
            timestamp=timestamp, domain_id=self.domain_id, site_id=site_id,
            asset_id=machine_id, variable="scrap_count_total",
            value=machine.counters.scrap_count_total, unit="pcs",
            data_type=DataType.INTEGER, point_type=PointType.SENSOR,
            pvn=build_pvn(machine_id, "scrap_count_total"),
        )
        
        yield DataPoint(
            timestamp=timestamp, domain_id=self.domain_id, site_id=site_id,
            asset_id=machine_id, variable="rework_count_total",
            value=machine.counters.rework_count_total, unit="pcs",
            data_type=DataType.INTEGER, point_type=PointType.SENSOR,
            pvn=build_pvn(machine_id, "rework_count_total"),
        )
        
        yield DataPoint(
            timestamp=timestamp, domain_id=self.domain_id, site_id=site_id,
            asset_id=machine_id, variable="last_cycle_time_s",
            value=round(machine.cycle.last_cycle_time_s, 2), unit="s",
            data_type=DataType.FLOAT, point_type=PointType.SENSOR,
            pvn=build_pvn(machine_id, "last_cycle_time_s"),
        )
        
        yield DataPoint(
            timestamp=timestamp, domain_id=self.domain_id, site_id=site_id,
            asset_id=machine_id, variable="ideal_cycle_time_sp",
            value=round(machine.ideal_cycle_time_sp, 2), unit="s",
            data_type=DataType.FLOAT, point_type=PointType.SETPOINT,
            pvn=build_pvn(machine_id, "ideal_cycle_time_sp"),
        )
        
        # === C) Energy signals ===
        yield DataPoint(
            timestamp=timestamp, domain_id=self.domain_id, site_id=site_id,
            asset_id=machine_id, variable="power_kw",
            value=round(machine.energy.power_kw, 3), unit="kW",
            data_type=DataType.FLOAT, point_type=PointType.SENSOR,
            pvn=build_pvn(machine_id, "power_kw"),
        )
        
        yield DataPoint(
            timestamp=timestamp, domain_id=self.domain_id, site_id=site_id,
            asset_id=machine_id, variable="energy_kwh_total",
            value=round(machine.energy.energy_kwh_total, 3), unit="kWh",
            data_type=DataType.FLOAT, point_type=PointType.SENSOR,
            pvn=build_pvn(machine_id, "energy_kwh_total"),
        )
        
        yield DataPoint(
            timestamp=timestamp, domain_id=self.domain_id, site_id=site_id,
            asset_id=machine_id, variable="voltage_v",
            value=round(machine.energy.voltage_v, 1), unit="V",
            data_type=DataType.FLOAT, point_type=PointType.SENSOR,
            pvn=build_pvn(machine_id, "voltage_v"),
        )
        
        yield DataPoint(
            timestamp=timestamp, domain_id=self.domain_id, site_id=site_id,
            asset_id=machine_id, variable="power_factor",
            value=round(machine.energy.power_factor, 3), unit="",
            data_type=DataType.FLOAT, point_type=PointType.SENSOR,
            pvn=build_pvn(machine_id, "power_factor"),
        )
        
        # === D) Condition signals ===
        yield DataPoint(
            timestamp=timestamp, domain_id=self.domain_id, site_id=site_id,
            asset_id=machine_id, variable="motor_temp_c",
            value=round(machine.condition.motor_temp_c, 1), unit="C",
            data_type=DataType.FLOAT, point_type=PointType.SENSOR,
            pvn=build_pvn(machine_id, "motor_temp_c"),
        )
        
        yield DataPoint(
            timestamp=timestamp, domain_id=self.domain_id, site_id=site_id,
            asset_id=machine_id, variable="vibration_rms_mm_s",
            value=round(machine.condition.vibration_rms_mm_s, 3), unit="mm/s",
            data_type=DataType.FLOAT, point_type=PointType.SENSOR,
            pvn=build_pvn(machine_id, "vibration_rms_mm_s"),
        )
        
        yield DataPoint(
            timestamp=timestamp, domain_id=self.domain_id, site_id=site_id,
            asset_id=machine_id, variable="load_factor",
            value=round(machine.condition.load_factor, 3), unit="",
            data_type=DataType.FLOAT, point_type=PointType.SENSOR,
            pvn=build_pvn(machine_id, "load_factor"),
        )
        
        if machine.config.has_pneumatics:
            yield DataPoint(
                timestamp=timestamp, domain_id=self.domain_id, site_id=site_id,
                asset_id=machine_id, variable="air_pressure_bar",
                value=round(machine.condition.air_pressure_bar, 2), unit="bar",
                data_type=DataType.FLOAT, point_type=PointType.SENSOR,
                pvn=build_pvn(machine_id, "air_pressure_bar"),
            )
        
        # === E) Context signals ===
        yield DataPoint(
            timestamp=timestamp, domain_id=self.domain_id, site_id=site_id,
            asset_id=machine_id, variable="product_code",
            value=machine.product_id or "", unit="",
            data_type=DataType.STRING, point_type=PointType.SENSOR,
            pvn=build_pvn(machine_id, "product_code"),
        )
        
        yield DataPoint(
            timestamp=timestamp, domain_id=self.domain_id, site_id=site_id,
            asset_id=machine_id, variable="order_id",
            value=machine.order_id or "", unit="",
            data_type=DataType.STRING, point_type=PointType.SENSOR,
            pvn=build_pvn(machine_id, "order_id"),
        )
        
        # === F) Data quality ===
        yield DataPoint(
            timestamp=timestamp, domain_id=self.domain_id, site_id=site_id,
            asset_id=machine_id, variable="data_quality",
            value=machine.data_quality, unit="",
            data_type=DataType.STRING, point_type=PointType.SENSOR,
            pvn=build_pvn(machine_id, "data_quality"),
        )

    def get_required_config_keys(self) -> list[str]:
        """Required configuration keys for Discrete Manufacturing."""
        return []

    def validate_config(self, project_cfg: dict[str, Any], domain_cfg: dict[str, Any]) -> list[str]:
        """Validate Discrete Manufacturing configuration."""
        errors = super().validate_config(project_cfg, domain_cfg)
        
        simulation = project_cfg.get("simulation", {})
        n_machines = simulation.get("n_machines", 8)
        
        if n_machines <= 0:
            errors.append("simulation.n_machines must be > 0")
        if n_machines > 13:
            errors.append("simulation.n_machines must be <= 13")
        
        return errors
