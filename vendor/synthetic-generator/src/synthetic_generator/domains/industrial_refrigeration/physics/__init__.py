"""Physics models for Industrial Refrigeration domain.

Contains simulation models for:
- Meteo (outdoor weather conditions)
- Chambers (cold room thermal dynamics)
- Compressors (rack staging and pressure control)
- Condenser (VFD control for discharge pressure)
- Separators (level dynamics)
- Pumps (lead-lag control)
- Energy (power consumption and metering)
"""

from .meteo import MeteoDriver, generate_synthetic_weather
from .chambers import ChamberSimulator, ChamberState
from .compressors import CompressorRackSimulator, CompressorRackState
from .condenser import CondenserSimulator, CondenserState
from .separators import SeparatorSimulator, SeparatorState
from .pumps import PumpSimulator, PumpState
from .energy import EnergyMeterSimulator, EnergyState

__all__ = [
    # Meteo
    "MeteoDriver",
    "generate_synthetic_weather",
    # Chambers
    "ChamberSimulator",
    "ChamberState",
    # Compressors
    "CompressorRackSimulator",
    "CompressorRackState",
    # Condenser
    "CondenserSimulator",
    "CondenserState",
    # Separators
    "SeparatorSimulator",
    "SeparatorState",
    # Pumps
    "PumpSimulator",
    "PumpState",
    # Energy
    "EnergyMeterSimulator",
    "EnergyState",
]
