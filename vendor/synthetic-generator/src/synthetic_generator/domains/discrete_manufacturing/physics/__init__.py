"""Physics simulation modules for discrete manufacturing.

Modules:
- machine: State machine with boolean output
- energy: Power and energy simulation  
- condition: Temperature, vibration, wear
- production: Cycles and counters with pieces_per_cycle support
- scheduling: Shift calendar
"""

from .machine import MachineStateMachine, TransitionContext
from .energy import EnergySimulator
from .condition import ConditionSimulator
from .production import ProductionSimulator
from .scheduling import Scheduler, ShiftCalendar

__all__ = [
    "MachineStateMachine",
    "TransitionContext",
    "EnergySimulator",
    "ConditionSimulator", 
    "ProductionSimulator",
    "Scheduler",
    "ShiftCalendar",
]
