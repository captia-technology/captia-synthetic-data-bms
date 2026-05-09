"""Discrete Manufacturing domain.

Generates synthetic OT telemetry for manufacturing plants.
Key features:
- Configurable machines with WISE 6DI boolean signals
- machine_state as BOOLEAN (true=RUN, false=STOP), NOT string
- Support for pieces_per_cycle (e.g., welding robot with 11 pieces per cycle)
- Physics-correlated signals (power/temp/vibration vs state)
- NO KPIs - only raw primary signals

CRITICAL: All state signals (machine_state, fault_active, estop_active, etc.)
are BOOLEAN, not strings. This matches the WISE 6DI digital input model.
"""

from .plugin import DiscreteManufacturingPlugin

__all__ = ["DiscreteManufacturingPlugin"]
