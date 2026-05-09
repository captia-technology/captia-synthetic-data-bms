"""State definitions for discrete manufacturing simulation.

Defines machine states with BOOLEAN outputs for WISE 6DI compatibility.
Internal state enum is used for logic; published machine_state is BOOLEAN.

CRITICAL DESIGN DECISION:
- Internal state: enum (OFF, IDLE, RUN, SETUP, STOP_PLANNED, STOP_UNPLANNED, MAINTENANCE)
- Published machine_state: BOOLEAN (true=RUN, false=STOP)
- This matches the WISE 6DI digital input model where marcha/paro is a boolean signal.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class InternalMachineState(str, Enum):
    """Internal machine operating states (NOT published directly).
    
    These are used internally for simulation logic.
    The published machine_state signal is BOOLEAN (is_running).
    """
    OFF = "OFF"
    IDLE = "IDLE"
    RUN = "RUN"
    SETUP = "SETUP"
    STOP_PLANNED = "STOP_PLANNED"
    STOP_UNPLANNED = "STOP_UNPLANNED"
    MAINTENANCE = "MAINTENANCE"


class MaintenanceType(str, Enum):
    """Maintenance type classification."""
    NONE = "NONE"
    PREVENTIVE = "PREVENTIVE"
    CORRECTIVE = "CORRECTIVE"


class StopReason(str, Enum):
    """Stop reason codes (used for analytics, not published as primary)."""
    NONE = "NONE"
    CHANGEOVER = "CHANGEOVER"
    MATERIAL_STARVE = "MATERIAL_STARVE"
    JAM = "JAM"
    SENSOR_FAIL = "SENSOR_FAIL"
    AIR_PRESSURE = "AIR_PRESSURE"
    OVERTEMP = "OVERTEMP"
    MOTOR_FAULT = "MOTOR_FAULT"
    TOOL_BREAK = "TOOL_BREAK"
    QUALITY_HOLD = "QUALITY_HOLD"
    OPERATOR_BREAK = "OPERATOR_BREAK"
    SHIFT_END = "SHIFT_END"
    PM = "PM"
    BREAKDOWN = "BREAKDOWN"
    EMERGENCY_STOP = "EMERGENCY_STOP"


@dataclass
class DISignals:
    """WISE 6DI Digital Input signals - ALL BOOLEANS.
    
    These represent the 6 digital inputs per machine:
    - DI1: machine_state (marcha/paro) - true=RUN
    - DI2: fault_active - true=fault present
    - DI3: estop_active - true=emergency stop engaged
    - DI4: cycle_in_progress - true during active cycle
    - DI5: material_present - true=material detected
    - DI6: operator_present - true=operator at station
    
    Additional derived boolean:
    - setup_active: true during setup/changeover
    """
    machine_state: bool = False     # DI1: true=RUN, false=STOP
    fault_active: bool = False      # DI2
    estop_active: bool = False      # DI3
    cycle_in_progress: bool = False # DI4
    material_present: bool = True   # DI5
    operator_present: bool = False  # DI6
    setup_active: bool = False      # Derived from internal state


@dataclass
class CycleState:
    """State for cycle tracking."""
    in_progress: bool = False
    start_time: Optional[datetime] = None
    elapsed_s: float = 0.0
    target_duration_s: float = 0.0
    last_cycle_time_s: float = 0.0
    

@dataclass
class ProductionCounters:
    """Production counters (monotonic).
    
    Naming convention:
    - cycle_count_total: total completed cycles
    - good_count_total: total good pieces
    - scrap_count_total: total scrap pieces
    - rework_count_total: total rework pieces
    
    Note: For machines with pieces_per_cycle > 1 (e.g. welding robot with 11),
    good+scrap+rework = cycle_count_total * pieces_per_cycle
    """
    cycle_count_total: int = 0
    good_count_total: int = 0
    scrap_count_total: int = 0
    rework_count_total: int = 0
    cycles_since_setup: int = 0


@dataclass
class EnergyState:
    """Energy metering state."""
    power_kw: float = 0.0
    energy_kwh_total: float = 0.0
    voltage_v: float = 400.0
    power_factor: float = 0.85
    startup_transient_remaining: int = 0
    last_power_kw: float = 0.0


@dataclass
class ConditionState:
    """Condition monitoring state."""
    load_factor: float = 0.0
    motor_temp_c: float = 25.0
    vibration_rms_mm_s: float = 0.5
    tool_wear_index: float = 0.0
    air_pressure_bar: float = 6.0
    air_pressure_drop_remaining: int = 0


@dataclass
class MaintenanceState:
    """Maintenance state."""
    active: bool = False
    maintenance_type: MaintenanceType = MaintenanceType.NONE
    workorder_id: str = ""
    remaining_duration_s: float = 0.0
    hours_since_last_pm: float = 0.0
    cycles_since_last_pm: int = 0


@dataclass
class MachineConfig:
    """Configuration for a single machine based on archetype."""
    machine_id: str
    archetype: str
    machine_name: str
    pieces_per_cycle: int  # Supports multiple pieces per cycle (e.g. welding robot)
    cycle_time_ideal_s: float
    idle_power_kw: float
    run_power_kw: float
    startup_spike_factor: float
    thermal_tau_minutes: float
    vibration_base: float
    vibration_load_gain: float
    vibration_wear_gain: float
    fault_base_rate: float
    fault_wear_gain: float
    microstop_rate: float
    setup_time_mean: float
    setup_time_std: float
    pm_interval_hours: float
    pm_duration_mean: float
    pm_duration_std: float
    nominal_scrap_rate: float
    nominal_rework_rate: float
    has_pneumatics: bool
    has_coolant: bool = False


@dataclass
class MachineState:
    """Complete state for a single machine.
    
    Key features:
    - Uses InternalMachineState for logic
    - Publishes machine_state as BOOLEAN via DISignals
    - Supports pieces_per_cycle for multi-piece operations
    """
    machine_id: str
    config: MachineConfig

    # Internal operating state (for simulation logic)
    internal_state: InternalMachineState = InternalMachineState.OFF
    previous_state: InternalMachineState = InternalMachineState.OFF
    state_duration_s: float = 0.0
    stop_reason: StopReason = StopReason.NONE
    fault_code: str = ""

    # WISE 6DI signals (BOOLEANS)
    di_signals: DISignals = field(default_factory=DISignals)

    # Production context
    order_id: str = ""
    product_id: str = ""
    ideal_cycle_time_sp: float = 45.0

    # Substates
    cycle: CycleState = field(default_factory=CycleState)
    counters: ProductionCounters = field(default_factory=ProductionCounters)
    energy: EnergyState = field(default_factory=EnergyState)
    condition: ConditionState = field(default_factory=ConditionState)
    maintenance: MaintenanceState = field(default_factory=MaintenanceState)

    # Event tracking
    setup_remaining_s: float = 0.0
    microstop_remaining_s: float = 0.0
    fault_remaining_s: float = 0.0
    planned_stop_remaining_s: float = 0.0
    material_starving_remaining_s: float = 0.0

    # Data quality
    data_quality: str = "OK"

    def update_di_signals(self):
        """Update DI signals based on internal state.
        
        This is the key mapping from internal state to boolean outputs:
        - machine_state = (internal_state == RUN)
        - setup_active = (internal_state == SETUP)
        - fault_active = (internal_state == STOP_UNPLANNED) or has fault
        - cycle_in_progress from cycle state
        """
        self.di_signals.machine_state = (self.internal_state == InternalMachineState.RUN)
        self.di_signals.setup_active = (self.internal_state == InternalMachineState.SETUP)
        self.di_signals.fault_active = (
            self.internal_state == InternalMachineState.STOP_UNPLANNED 
            or bool(self.fault_code)
        )
        self.di_signals.cycle_in_progress = self.cycle.in_progress
        # material_present and operator_present are updated by the state machine
        # estop_active is a separate event trigger


@dataclass
class PlantState:
    """Aggregated state for the plant."""
    machines: dict[str, MachineState] = field(default_factory=dict)
    current_time: Optional[datetime] = None
    shift_active: bool = False
    break_active: bool = False

    def get_machine(self, machine_id: str) -> Optional[MachineState]:
        """Get machine state by ID."""
        return self.machines.get(machine_id)

    def get_running_count(self) -> int:
        """Count machines in RUN state."""
        return sum(
            1 for m in self.machines.values() 
            if m.di_signals.machine_state  # Uses boolean directly
        )

    def get_total_power_kw(self) -> float:
        """Get total power consumption."""
        return sum(m.energy.power_kw for m in self.machines.values())
