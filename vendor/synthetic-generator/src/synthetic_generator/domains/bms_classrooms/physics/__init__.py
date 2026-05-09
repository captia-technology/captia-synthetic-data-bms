"""Physics models for BMS Classrooms domain.

Contains simulation models for:
- Environment (outdoor temperature, daylight)
- Occupancy (capacity, utilization)
- Indoor conditions (temperature, CO2, humidity, noise, illuminance)
- Actuators (HVAC, lighting, scenes)
- Energy (power consumption)
"""

from .environment import outdoor_temperature, daylight_lux
from .occupancy import sample_aula_parameters, generate_occupancy_count
from .indoor import (
    simulate_indoor_temperature,
    simulate_co2,
    simulate_humidity,
    simulate_noise,
    simulate_illuminance,
    derive_pir_presence,
)
from .actuators import (
    derive_scene,
    thermostat_setpoint,
    hvac_mode,
    hvac_enable,
    heating_valve_position,
    light_state,
)
from .energy import simulate_power, integrate_energy_kwh

__all__ = [
    # Environment
    "outdoor_temperature",
    "daylight_lux",
    # Occupancy
    "sample_aula_parameters",
    "generate_occupancy_count",
    # Indoor
    "simulate_indoor_temperature",
    "simulate_co2",
    "simulate_humidity",
    "simulate_noise",
    "simulate_illuminance",
    "derive_pir_presence",
    # Actuators
    "derive_scene",
    "thermostat_setpoint",
    "hvac_mode",
    "hvac_enable",
    "heating_valve_position",
    "light_state",
    # Energy
    "simulate_power",
    "integrate_energy_kwh",
]
