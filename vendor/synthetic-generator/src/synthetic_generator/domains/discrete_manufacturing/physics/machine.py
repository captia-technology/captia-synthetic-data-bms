"""Machine state machine for discrete manufacturing.

Implements state transitions with BOOLEAN machine_state output.
Internal state is enum-based for logic; published signal is boolean.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np

from ..state import (
    MachineState,
    InternalMachineState,
    MaintenanceType,
    StopReason,
)

LOG = logging.getLogger("synthetic_generator.domains.discrete_manufacturing.machine")


@dataclass
class TransitionContext:
    """Context for state transitions."""
    dt_seconds: float
    shift_active: bool
    break_active: bool
    has_order: bool
    operator_present: bool
    air_pressure_ok: bool
    temp_ok: bool
    material_present: bool


class MachineStateMachine:
    """State machine for a manufacturing machine.
    
    Key feature: outputs machine_state as BOOLEAN.
    
    Handles transitions between states based on:
    - Shift calendar (operator presence)
    - Production orders
    - Faults and microstops
    - Maintenance (preventive/corrective)
    - Setup/changeover
    - Material presence (starving)
    """

    def __init__(self, physics_cfg: dict, anomaly_cfg: dict, rng: np.random.Generator):
        """Initialize state machine.
        
        Args:
            physics_cfg: Physics configuration dict
            anomaly_cfg: Anomaly/data quality configuration
            rng: NumPy random generator
        """
        self.physics_cfg = physics_cfg
        self.anomaly_cfg = anomaly_cfg
        self.rng = rng
        
        # Extract material starving config
        material_cfg = physics_cfg.get("material", {})
        self.starving_prob = material_cfg.get("starving_probability_per_hour", 0.05)
        self.starving_mean_s = material_cfg.get("starving_duration_s", {}).get("mean", 60)
        self.starving_std_s = material_cfg.get("starving_duration_s", {}).get("std", 30)

    def step(
        self,
        machine: MachineState,
        ctx: TransitionContext
    ) -> MachineState:
        """Execute one simulation step for state transitions.
        
        Args:
            machine: Current machine state
            ctx: Transition context
            
        Returns:
            Updated machine state
        """
        machine.previous_state = machine.internal_state
        machine.state_duration_s += ctx.dt_seconds
        
        # Update maintenance timer when running
        if machine.internal_state == InternalMachineState.RUN:
            machine.maintenance.hours_since_last_pm += ctx.dt_seconds / 3600.0
        
        # Update DI signals from context
        machine.di_signals.operator_present = ctx.operator_present
        machine.di_signals.material_present = ctx.material_present
        
        # Check for emergency stop (rare event)
        if self._check_estop(machine, ctx):
            machine.di_signals.estop_active = True
            self._transition_to(machine, InternalMachineState.STOP_UNPLANNED, StopReason.EMERGENCY_STOP)
            machine.update_di_signals()
            return machine
        else:
            machine.di_signals.estop_active = False
        
        # State-specific transitions
        if machine.internal_state == InternalMachineState.OFF:
            self._handle_off(machine, ctx)
        elif machine.internal_state == InternalMachineState.IDLE:
            self._handle_idle(machine, ctx)
        elif machine.internal_state == InternalMachineState.RUN:
            self._handle_run(machine, ctx)
        elif machine.internal_state == InternalMachineState.SETUP:
            self._handle_setup(machine, ctx)
        elif machine.internal_state == InternalMachineState.STOP_PLANNED:
            self._handle_stop_planned(machine, ctx)
        elif machine.internal_state == InternalMachineState.STOP_UNPLANNED:
            self._handle_stop_unplanned(machine, ctx)
        elif machine.internal_state == InternalMachineState.MAINTENANCE:
            self._handle_maintenance(machine, ctx)
        
        # Update DI signals after state changes
        machine.update_di_signals()
        
        return machine

    def _transition_to(
        self,
        machine: MachineState,
        new_state: InternalMachineState,
        stop_reason: StopReason = StopReason.NONE
    ):
        """Transition to a new state."""
        if machine.internal_state != new_state:
            LOG.debug(
                "Machine %s: %s -> %s (reason: %s)",
                machine.machine_id, machine.internal_state.value, 
                new_state.value, stop_reason.value
            )
            machine.internal_state = new_state
            machine.state_duration_s = 0.0
            machine.stop_reason = stop_reason
            
            # Reset cycle if not running
            if new_state != InternalMachineState.RUN:
                machine.cycle.in_progress = False

    def _check_estop(self, machine: MachineState, ctx: TransitionContext) -> bool:
        """Check for emergency stop (very rare)."""
        p_estop = 0.001 * ctx.dt_seconds / 3600.0
        return self.rng.random() < p_estop

    def _handle_off(self, machine: MachineState, ctx: TransitionContext):
        """Handle OFF state transitions."""
        if ctx.shift_active and ctx.operator_present and not ctx.break_active:
            self._transition_to(machine, InternalMachineState.IDLE)

    def _handle_idle(self, machine: MachineState, ctx: TransitionContext):
        """Handle IDLE state transitions."""
        if self._should_start_pm(machine):
            self._start_preventive_maintenance(machine)
            return
        
        if not ctx.shift_active:
            self._transition_to(machine, InternalMachineState.STOP_PLANNED, StopReason.SHIFT_END)
            return
        
        if ctx.break_active:
            self._transition_to(machine, InternalMachineState.STOP_PLANNED, StopReason.OPERATOR_BREAK)
            machine.planned_stop_remaining_s = 900
            return
        
        if ctx.has_order and ctx.operator_present:
            if machine.setup_remaining_s > 0:
                self._transition_to(machine, InternalMachineState.SETUP, StopReason.CHANGEOVER)
            else:
                if not ctx.air_pressure_ok and machine.config.has_pneumatics:
                    self._transition_to(machine, InternalMachineState.STOP_UNPLANNED, StopReason.AIR_PRESSURE)
                    machine.fault_remaining_s = self._sample_fault_duration(short=True)
                elif not ctx.temp_ok:
                    self._transition_to(machine, InternalMachineState.STOP_UNPLANNED, StopReason.OVERTEMP)
                    machine.fault_remaining_s = self._sample_fault_duration(short=True)
                elif not ctx.material_present:
                    self._transition_to(machine, InternalMachineState.STOP_UNPLANNED, StopReason.MATERIAL_STARVE)
                    machine.material_starving_remaining_s = max(
                        self.starving_mean_s + self.rng.normal(0, self.starving_std_s), 10
                    )
                else:
                    self._transition_to(machine, InternalMachineState.RUN)

    def _handle_run(self, machine: MachineState, ctx: TransitionContext):
        """Handle RUN state transitions."""
        if self._check_fault(machine, ctx):
            return
        if self._check_microstop(machine, ctx):
            return
        if self._check_starving(machine, ctx):
            return
        
        if ctx.break_active:
            self._transition_to(machine, InternalMachineState.STOP_PLANNED, StopReason.OPERATOR_BREAK)
            machine.planned_stop_remaining_s = 900
            return
        
        if not ctx.shift_active:
            self._transition_to(machine, InternalMachineState.STOP_PLANNED, StopReason.SHIFT_END)
            return
        
        if not ctx.has_order:
            self._transition_to(machine, InternalMachineState.IDLE)
            return
        
        if not ctx.air_pressure_ok and machine.config.has_pneumatics:
            self._transition_to(machine, InternalMachineState.STOP_UNPLANNED, StopReason.AIR_PRESSURE)
            machine.fault_remaining_s = self._sample_fault_duration(short=True)
            return
        
        if not ctx.temp_ok:
            self._transition_to(machine, InternalMachineState.STOP_UNPLANNED, StopReason.OVERTEMP)
            machine.fault_remaining_s = self._sample_fault_duration(short=True)
            return

    def _handle_setup(self, machine: MachineState, ctx: TransitionContext):
        """Handle SETUP state transitions."""
        machine.setup_remaining_s -= ctx.dt_seconds
        
        if machine.setup_remaining_s <= 0:
            machine.setup_remaining_s = 0
            machine.counters.cycles_since_setup = 0
            if ctx.has_order and ctx.operator_present and ctx.shift_active and not ctx.break_active:
                if ctx.material_present:
                    self._transition_to(machine, InternalMachineState.RUN)
                else:
                    self._transition_to(machine, InternalMachineState.IDLE)
            else:
                self._transition_to(machine, InternalMachineState.IDLE)

    def _handle_stop_planned(self, machine: MachineState, ctx: TransitionContext):
        """Handle STOP_PLANNED state transitions."""
        machine.planned_stop_remaining_s -= ctx.dt_seconds
        
        if machine.stop_reason == StopReason.OPERATOR_BREAK:
            if not ctx.break_active and ctx.shift_active:
                self._transition_to(machine, InternalMachineState.IDLE)
        elif machine.stop_reason == StopReason.SHIFT_END:
            if ctx.shift_active and ctx.operator_present:
                self._transition_to(machine, InternalMachineState.IDLE)
        elif machine.planned_stop_remaining_s <= 0:
            if ctx.shift_active and ctx.operator_present:
                self._transition_to(machine, InternalMachineState.IDLE)

    def _handle_stop_unplanned(self, machine: MachineState, ctx: TransitionContext):
        """Handle STOP_UNPLANNED state transitions."""
        if machine.stop_reason == StopReason.MATERIAL_STARVE:
            machine.material_starving_remaining_s -= ctx.dt_seconds
            if machine.material_starving_remaining_s <= 0 and ctx.material_present:
                machine.di_signals.material_present = True
                self._transition_to(machine, InternalMachineState.IDLE)
                return
        
        if machine.microstop_remaining_s > 0:
            machine.microstop_remaining_s -= ctx.dt_seconds
            if machine.microstop_remaining_s <= 0:
                machine.fault_code = ""
                self._transition_to(machine, InternalMachineState.IDLE)
                return
        
        if machine.fault_remaining_s > 0:
            machine.fault_remaining_s -= ctx.dt_seconds
            if machine.fault_remaining_s <= 0:
                if machine.fault_code:
                    self._start_corrective_maintenance(machine)
                else:
                    self._transition_to(machine, InternalMachineState.IDLE)

    def _handle_maintenance(self, machine: MachineState, ctx: TransitionContext):
        """Handle MAINTENANCE state transitions."""
        machine.maintenance.remaining_duration_s -= ctx.dt_seconds
        if machine.maintenance.remaining_duration_s <= 0:
            self._complete_maintenance(machine)

    def _check_fault(self, machine: MachineState, ctx: TransitionContext) -> bool:
        """Check for random fault occurrence."""
        cfg = machine.config
        fault_rate = cfg.fault_base_rate + cfg.fault_wear_gain * machine.condition.tool_wear_index
        p_fault = fault_rate * ctx.dt_seconds / 3600.0
        
        if self.rng.random() < p_fault:
            machine.fault_code = self._sample_fault_code()
            self._transition_to(machine, InternalMachineState.STOP_UNPLANNED, 
                              self._fault_to_stop_reason(machine.fault_code))
            machine.fault_remaining_s = self._sample_fault_duration(short=False)
            return True
        return False

    def _check_microstop(self, machine: MachineState, ctx: TransitionContext) -> bool:
        """Check for microstop occurrence."""
        cfg = machine.config
        p_microstop = cfg.microstop_rate * ctx.dt_seconds / 3600.0
        
        if self.rng.random() < p_microstop:
            stop_reasons = [StopReason.JAM, StopReason.QUALITY_HOLD]
            idx = self.rng.integers(0, len(stop_reasons))
            stop_reason = stop_reasons[idx]
            self._transition_to(machine, InternalMachineState.STOP_UNPLANNED, stop_reason)
            machine.microstop_remaining_s = self.rng.uniform(10, 120)
            return True
        return False

    def _check_starving(self, machine: MachineState, ctx: TransitionContext) -> bool:
        """Check for material starving."""
        p_starve = self.starving_prob * ctx.dt_seconds / 3600.0
        
        if self.rng.random() < p_starve:
            machine.di_signals.material_present = False
            self._transition_to(machine, InternalMachineState.STOP_UNPLANNED, StopReason.MATERIAL_STARVE)
            machine.material_starving_remaining_s = max(
                self.starving_mean_s + self.rng.normal(0, self.starving_std_s), 10
            )
            return True
        return False

    def _should_start_pm(self, machine: MachineState) -> bool:
        """Check if preventive maintenance should start."""
        return machine.maintenance.hours_since_last_pm >= machine.config.pm_interval_hours

    def _start_preventive_maintenance(self, machine: MachineState):
        """Start preventive maintenance."""
        cfg = machine.config
        machine.maintenance.active = True
        machine.maintenance.maintenance_type = MaintenanceType.PREVENTIVE
        machine.maintenance.workorder_id = f"PM_{machine.machine_id}_{int(machine.maintenance.hours_since_last_pm)}"
        duration = max(cfg.pm_duration_mean + self.rng.normal(0, cfg.pm_duration_std), cfg.pm_duration_mean * 0.5)
        machine.maintenance.remaining_duration_s = duration * 60
        self._transition_to(machine, InternalMachineState.MAINTENANCE, StopReason.PM)

    def _start_corrective_maintenance(self, machine: MachineState):
        """Start corrective maintenance after fault."""
        cfg = machine.config
        machine.maintenance.active = True
        machine.maintenance.maintenance_type = MaintenanceType.CORRECTIVE
        machine.maintenance.workorder_id = f"CM_{machine.machine_id}_{machine.fault_code}"
        duration = max(cfg.pm_duration_mean * 1.5 + self.rng.normal(0, cfg.pm_duration_std * 2), cfg.pm_duration_mean * 0.5)
        machine.maintenance.remaining_duration_s = duration * 60
        self._transition_to(machine, InternalMachineState.MAINTENANCE, StopReason.BREAKDOWN)

    def _complete_maintenance(self, machine: MachineState):
        """Complete maintenance and reset relevant states."""
        wear_cfg = self.physics_cfg.get("wear", {})
        reset_factor = wear_cfg.get("reset_after_maintenance", 0.08)
        
        if machine.maintenance.maintenance_type == MaintenanceType.PREVENTIVE:
            machine.condition.tool_wear_index *= reset_factor
        else:
            machine.condition.tool_wear_index *= reset_factor * 0.5
        
        machine.maintenance.active = False
        machine.maintenance.maintenance_type = MaintenanceType.NONE
        machine.maintenance.workorder_id = ""
        machine.maintenance.remaining_duration_s = 0
        machine.maintenance.hours_since_last_pm = 0
        machine.maintenance.cycles_since_last_pm = 0
        machine.fault_code = ""
        self._transition_to(machine, InternalMachineState.IDLE)

    def _sample_fault_duration(self, short: bool = False) -> float:
        """Sample fault duration in seconds."""
        if short:
            return self.rng.uniform(300, 1800)
        else:
            return self.rng.uniform(600, 10800)

    def _sample_fault_code(self) -> str:
        """Sample a random fault code."""
        codes = ["F001", "F002", "F003", "F004", "F005", "F006", "F007", "F008"]
        return self.rng.choice(codes)

    def _fault_to_stop_reason(self, fault_code: str) -> StopReason:
        """Map fault code to stop reason."""
        mapping = {
            "F001": StopReason.MOTOR_FAULT,
            "F002": StopReason.OVERTEMP,
            "F003": StopReason.SENSOR_FAIL,
            "F004": StopReason.AIR_PRESSURE,
            "F005": StopReason.TOOL_BREAK,
            "F006": StopReason.JAM,
            "F007": StopReason.MOTOR_FAULT,
            "F008": StopReason.SENSOR_FAIL,
        }
        return mapping.get(fault_code, StopReason.BREAKDOWN)

    def trigger_setup(self, machine: MachineState, new_product_id: str, new_order_id: str):
        """Trigger a setup/changeover for new product."""
        cfg = machine.config
        duration = max(cfg.setup_time_mean + self.rng.normal(0, cfg.setup_time_std), cfg.setup_time_mean * 0.3)
        machine.setup_remaining_s = duration * 60
        machine.product_id = new_product_id
        machine.order_id = new_order_id
