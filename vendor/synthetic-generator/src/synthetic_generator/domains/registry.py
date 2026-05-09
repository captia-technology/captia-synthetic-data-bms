"""Domain plugin registry.

Provides registration and discovery of domain plugins.
"""
from __future__ import annotations

from typing import Type, Optional
import logging

from .base import DomainPlugin

LOG = logging.getLogger("synthetic_generator.domains")

# Global plugin registry
_DOMAIN_REGISTRY: dict[str, Type[DomainPlugin]] = {}


def register_domain(cls: Type[DomainPlugin]) -> Type[DomainPlugin]:
    """Decorator to register a domain plugin.

    Use this decorator on domain plugin classes to automatically
    register them with the global registry.

    Example:
        @register_domain
        class BMSClassroomsPlugin(DomainPlugin):
            @property
            def domain_id(self) -> str:
                return "bms_classrooms"
            ...

    Args:
        cls: Domain plugin class to register

    Returns:
        The same class (allows use as decorator)
    """
    # Create temporary instance to get domain_id
    try:
        instance = cls()
        domain_id = instance.domain_id
    except Exception as e:
        LOG.warning(f"Could not instantiate plugin {cls.__name__} for registration: {e}")
        return cls

    if domain_id in _DOMAIN_REGISTRY:
        LOG.warning(f"Overwriting existing domain plugin: {domain_id}")

    _DOMAIN_REGISTRY[domain_id] = cls
    LOG.debug(f"Registered domain plugin: {domain_id}")

    return cls


def get_domain(domain_id: str) -> Optional[DomainPlugin]:
    """Get a domain plugin instance by ID.

    Args:
        domain_id: Domain identifier

    Returns:
        Instance of the domain plugin, or None if not found
    """
    cls = _DOMAIN_REGISTRY.get(domain_id)
    if cls is None:
        LOG.error(f"Unknown domain: {domain_id}. Available: {list_domains()}")
        return None
    return cls()


def get_domain_class(domain_id: str) -> Optional[Type[DomainPlugin]]:
    """Get a domain plugin class by ID.

    Args:
        domain_id: Domain identifier

    Returns:
        Domain plugin class, or None if not found
    """
    return _DOMAIN_REGISTRY.get(domain_id)


def list_domains() -> list[str]:
    """List all registered domain IDs.

    Returns:
        List of domain ID strings
    """
    return list(_DOMAIN_REGISTRY.keys())


def list_domain_info() -> list[dict]:
    """List metadata for all registered domains.

    Returns:
        List of metadata dictionaries for each domain
    """
    info = []
    for domain_id in _DOMAIN_REGISTRY:
        plugin = get_domain(domain_id)
        if plugin:
            info.append(plugin.get_metadata())
    return info


def is_registered(domain_id: str) -> bool:
    """Check if a domain is registered.

    Args:
        domain_id: Domain identifier

    Returns:
        True if domain is registered
    """
    return domain_id in _DOMAIN_REGISTRY


def unregister_domain(domain_id: str) -> bool:
    """Unregister a domain plugin.

    Primarily useful for testing.

    Args:
        domain_id: Domain identifier to unregister

    Returns:
        True if domain was unregistered, False if not found
    """
    if domain_id in _DOMAIN_REGISTRY:
        del _DOMAIN_REGISTRY[domain_id]
        LOG.debug(f"Unregistered domain plugin: {domain_id}")
        return True
    return False


def clear_registry():
    """Clear all registered domains.

    Primarily useful for testing.
    """
    _DOMAIN_REGISTRY.clear()


def auto_discover_domains():
    """Auto-discover and register domain plugins.

    Imports known domain modules to trigger registration.
    Call this at application startup.

    NOTE (CAPTIA-SYNTHETIC-DATA-BMS): This vendor build only ships the
    `bms_classrooms` domain. See PATCHES/001-bms-only.patch.
    """
    try:
        from ..domains import bms_classrooms  # noqa: F401
        LOG.debug("Loaded bms_classrooms domain")
    except ImportError as e:
        LOG.debug(f"Could not load bms_classrooms domain: {e}")
