"""Industrial Refrigeration domain.

Provides synthetic data generation for cold storage facilities:
- Cold chambers with thermal dynamics and evaporator control
- Compressor rack with staging and pressure control
- Condenser with VFD control
- Separator vessels and circulation pumps
- Energy metering with phase balance
- Weather conditions

Usage:
    from synthetic_generator.domains import get_domain

    plugin = get_domain("industrial_refrigeration")
    inventory = plugin.build_inventory(project_cfg, domain_cfg)
    ctx = plugin.build_context(time_index, project_cfg, domain_cfg, rng)
    for point in plugin.simulate(time_index, inventory, ctx, rng):
        process(point)
"""

from .plugin import IndustrialRefrigerationPlugin
from .inventory import build_refrigeration_inventory
from .context import build_refrigeration_context, RefrigerationContext
from .state import PlantState
from .calibration import calibrate_from_sample

__all__ = [
    "IndustrialRefrigerationPlugin",
    "build_refrigeration_inventory",
    "build_refrigeration_context",
    "RefrigerationContext",
    "PlantState",
    "calibrate_from_sample",
]
