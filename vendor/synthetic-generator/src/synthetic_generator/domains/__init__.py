"""Domain plugin framework for multi-domain synthetic data generation.

This module provides the plugin architecture for domain-specific
data generation:
- Base plugin interface (DomainPlugin)
- Plugin registry with auto-discovery
- Domain-specific implementations (bms_classrooms, industrial_refrigeration)

Usage:
    from synthetic_generator.domains import get_domain, list_domains

    # List available domains
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
