"""Context builder for discrete manufacturing domain.

Initializes simulation state and schedulers.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from .state import (
    MachineState,
    PlantState,
    MachineConfig,
    InternalMachineState,
    DISignals,
    CycleState,
    ProductionCounters,
    EnergyState,
    ConditionState,
    MaintenanceState,
)
from .physics.scheduling import Scheduler, ShiftCalendar

LOG = logging.getLogger("synthetic_generator.domains.discrete_manufacturing.context")


@dataclass
class ManufacturingContext:
    """Simulation context for manufacturing plant."""
    plant_state: PlantState
    scheduler: Scheduler
    physics_cfg: dict
    anomaly_cfg: dict
    product_catalog: dict
    machine_configs: dict[str, MachineConfig] = field(default_factory=dict)


def build_manufacturing_context(
    time_index: pd.DatetimeIndex,
    project_cfg: dict[str, Any],
    domain_cfg: dict[str, Any],
    machine_configs: dict[str, MachineConfig],
    rng: np.random.Generator
) -> ManufacturingContext:
    """Build simulation context for manufacturing plant.
    
    Args:
        time_index: Time points for simulation
        project_cfg: Project configuration
        domain_cfg: Domain configuration
        machine_configs: Machine configurations
        rng: NumPy random generator
        
    Returns:
        ManufacturingContext with initialized state
    """
    # Extract configs
    physics_cfg = domain_cfg.get("physics", {})
    anomaly_cfg = domain_cfg.get("anomalies", {})
    product_catalog = domain_cfg.get("product_catalog", {})
    calendar_cfg = domain_cfg.get("shift_calendar", {})
    scheduling_cfg = domain_cfg.get("scheduling", {})
    
    # Initialize shift calendar
    calendar = ShiftCalendar(calendar_cfg, rng)
    
    # Initialize scheduler
    scheduler = Scheduler(
        calendar=calendar,
        product_catalog=product_catalog,
        scheduling_cfg=scheduling_cfg,
        rng=rng
    )
    
    # Initialize plant state with machines
    plant_state = PlantState()
    
    for machine_id, config in machine_configs.items():
        machine = _init_machine_state(machine_id, config, physics_cfg)
        plant_state.machines[machine_id] = machine
    
    LOG.info(
        "Built manufacturing context with %d machines",
        len(plant_state.machines)
    )
    
    return ManufacturingContext(
        plant_state=plant_state,
        scheduler=scheduler,
        physics_cfg=physics_cfg,
        anomaly_cfg=anomaly_cfg,
        product_catalog=product_catalog,
        machine_configs=machine_configs,
    )


def _init_machine_state(
    machine_id: str,
    config: MachineConfig,
    physics_cfg: dict
) -> MachineState:
    """Initialize a single machine state.
    
    Args:
        machine_id: Machine identifier
        config: Machine configuration
        physics_cfg: Physics configuration
        
    Returns:
        Initialized MachineState
    """
    thermal_cfg = physics_cfg.get("thermal", {})
    motor_cfg = thermal_cfg.get("motor_temp", {})
    air_cfg = physics_cfg.get("air_pressure", {})
    
    # Initialize condition state
    condition = ConditionState(
        load_factor=0.0,
        motor_temp_c=motor_cfg.get("initial_c", 25),
        vibration_rms_mm_s=config.vibration_base * 0.1,
        tool_wear_index=0.0,
        air_pressure_bar=air_cfg.get("nominal_bar", 6.0) if config.has_pneumatics else 0.0,
    )
    
    # Initialize energy state
    energy = EnergyState(
        power_kw=0.0,
        energy_kwh_total=0.0,
        voltage_v=physics_cfg.get("electrical", {}).get("nominal_voltage_v", 400),
        power_factor=0.0,
    )
    
    machine = MachineState(
        machine_id=machine_id,
        config=config,
        internal_state=InternalMachineState.OFF,
        di_signals=DISignals(),
        cycle=CycleState(),
        counters=ProductionCounters(),
        energy=energy,
        condition=condition,
        maintenance=MaintenanceState(),
        ideal_cycle_time_sp=config.cycle_time_ideal_s,
    )
    
    return machine
