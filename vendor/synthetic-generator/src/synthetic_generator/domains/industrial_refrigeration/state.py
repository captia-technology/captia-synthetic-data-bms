"""Plant state management for Industrial Refrigeration.

Provides centralized state container for all plant components.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .physics.chambers import ChamberState
from .physics.compressors import CompressorRackState
from .physics.condenser import CondenserState
from .physics.separators import SeparatorState
from .physics.pumps import PumpState
from .physics.energy import EnergyState


@dataclass
class PlantState:
    """Complete state of the refrigeration plant.

    Contains state for all subsystems: chambers, compressors,
    condenser, separators, pumps, and energy metering.
    """
    # Chamber states (keyed by chamber_id)
    chambers: dict[str, ChamberState] = field(default_factory=dict)

    # Central systems
    compressor_rack: CompressorRackState = field(default_factory=CompressorRackState)
    condenser: CondenserState = field(default_factory=CondenserState)

    # Separators
    separator_high: SeparatorState = field(default_factory=lambda: SeparatorState(separator_id="ALTA"))
    separator_low: SeparatorState = field(default_factory=lambda: SeparatorState(separator_id="BAJA"))

    # Pumps
    pumps: PumpState = field(default_factory=PumpState)

    # Energy metering
    energy: EnergyState = field(default_factory=EnergyState)

    def get_total_cooling_demand(self) -> float:
        """Calculate total cooling demand from all chambers.

        Returns normalized demand (0-1) based on active evaporators.
        """
        if not self.chambers:
            return 0.0

        total_evaps = 0
        active_evaps = 0

        for chamber in self.chambers.values():
            total_evaps += 2  # Each chamber has 2 potential evaporators
            if chamber.evap1_cooling_cmd:
                active_evaps += 1
            if chamber.evap2_cooling_cmd:
                active_evaps += 1

        return active_evaps / max(1, total_evaps)

    def get_average_chamber_error(self) -> float:
        """Calculate average temperature error across chambers."""
        if not self.chambers:
            return 0.0

        errors = [
            abs(c.temperature - c.setpoint)
            for c in self.chambers.values()
        ]
        return sum(errors) / len(errors)

    def get_system_activity(self) -> float:
        """Get overall system activity level (0-1)."""
        n_compressors_on = sum(self.compressor_rack.compressor_states.values())
        max_compressors = len(self.compressor_rack.compressor_states)
        return n_compressors_on / max(1, max_compressors)
