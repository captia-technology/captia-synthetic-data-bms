"""BMS Classrooms domain.

Provides synthetic data generation for school classroom building management:
- Environmental monitoring (temperature, CO2, humidity, noise, illuminance)
- Occupancy detection
- HVAC control
- Lighting control
- Energy metering

Usage:
    from synthetic_generator.domains import get_domain

    plugin = get_domain("bms_classrooms")
    inventory = plugin.build_inventory(project_cfg, domain_cfg)
    ctx = plugin.build_context(time_index, project_cfg, domain_cfg, rng)
    for point in plugin.simulate(time_index, inventory, ctx, rng):
        process(point)
"""

from .plugin import BMSClassroomsPlugin
from .inventory import build_bms_inventory
from .context import build_bms_context, BMSClassroomsContext

__all__ = [
    "BMSClassroomsPlugin",
    "build_bms_inventory",
    "build_bms_context",
    "BMSClassroomsContext",
]
