"""Domain plugin framework for synthetic data generation.

This vendor build (CAPTIA-SYNTHETIC-DATA-BMS) only ships the
`bms_classrooms` domain. See `vendor/synthetic-generator/PATCHES/`.

Usage:
    from synthetic_generator.domains import get_domain, list_domains

    # List available domains (currently: bms_classrooms)
    domains = list_domains()

    # Get a domain plugin
    plugin = get_domain("bms_classrooms")

    # Generate data
    inventory = plugin.build_inventory(project_cfg, domain_cfg)
    ctx = plugin.build_context(time_index, project_cfg, domain_cfg, rng)
    for point in plugin.simulate(time_index, inventory, ctx, rng):
        process(point)
"""

from .base import DomainPlugin
from .registry import (
    register_domain,
    get_domain,
    get_domain_class,
    list_domains,
    list_domain_info,
    is_registered,
    unregister_domain,
    clear_registry,
    auto_discover_domains,
)

__all__ = [
    "DomainPlugin",
    "register_domain",
    "get_domain",
    "get_domain_class",
    "list_domains",
    "list_domain_info",
    "is_registered",
    "unregister_domain",
    "clear_registry",
    "auto_discover_domains",
]
