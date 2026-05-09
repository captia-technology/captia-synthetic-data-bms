"""PV (Point Variable) naming and MQTT topic construction.

CAPTIA namespace: captia/{env}/{tenant}/{site}/{device}/{stream}/{name}
"""
from __future__ import annotations

from typing import Optional


def build_pvn(asset_id: str, variable: str) -> str:
    """
    Build Point Variable Name: {ASSET_ID}__{variable}.

    Args:
        asset_id: Asset identifier (uppercase)
        variable: Variable name (lowercase)

    Returns:
        PVN string
    """
    return f"{asset_id.upper()}__{variable.lower()}"


def build_pvp(
    namespace: str,
    modo: str,
    schema_version: str,
    site_id: str,
    asset_id: str,
    variable: str,
) -> str:
    """
    Build Point Variable Path: {ns}/{modo}/{schema}/{site}/{asset}/{var}.

    Args:
        namespace: Project namespace
        modo: Mode (e.g., 'synthetic', 'production')
        schema_version: Schema version (e.g., 'v0.1')
        site_id: Site identifier
        asset_id: Asset identifier (uppercase)
        variable: Variable name (lowercase)

    Returns:
        PVP string
    """
    return f"{namespace}/{modo}/{schema_version}/{site_id}/{asset_id.upper()}/{variable.lower()}"


def parse_pvn(pvn: str) -> tuple[str, str]:
    """
    Parse Point Variable Name into asset_id and variable.

    Args:
        pvn: PVN string in format {ASSET_ID}__{variable}

    Returns:
        Tuple of (asset_id, variable)

    Raises:
        ValueError: If PVN format is invalid
    """
    parts = pvn.split("__", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid PVN format: {pvn}")
    return parts[0].upper(), parts[1].lower()


def parse_pvp(pvp: str) -> dict[str, str]:
    """
    Parse Point Variable Path into components.

    Args:
        pvp: PVP string in format {ns}/{modo}/{schema}/{site}/{asset}/{var}

    Returns:
        Dictionary with keys: namespace, modo, schema_version, site_id, asset_id, variable

    Raises:
        ValueError: If PVP format is invalid
    """
    parts = pvp.split("/")
    if len(parts) != 6:
        raise ValueError(f"Invalid PVP format: {pvp}")

    return {
        "namespace": parts[0],
        "modo": parts[1],
        "schema_version": parts[2],
        "site_id": parts[3],
        "asset_id": parts[4].upper(),
        "variable": parts[5].lower(),
    }


# ---------------------------------------------------------------------------
# CAPTIA namespace helpers
# ---------------------------------------------------------------------------


def build_captia_mqtt_topic(
    *,
    env: str = "dev",
    tenant: str = "default",
    site: str,
    device: str,
    stream: str = "telemetry",
    name: str,
    prefix: str = "captia",
    version: Optional[str] = None,
) -> str:
    """Build topic using CAPTIA namespace: captia/{env}/{tenant}/{site}/{device}/{stream}/{name}.

    Args:
        env: Environment slug (prod/staging/dev/test/sandbox).
        tenant: Tenant slug.
        site: Site identifier.
        device: Device / asset identifier.
        stream: One of telemetry/state/event/cmd/ack/meta.
        name: Leaf — metric, command, event type.
        prefix: Root prefix (default "captia").
        version: Optional version slug (e.g. "v1").

    Returns:
        Fully-qualified MQTT topic.
    """
    segments = [prefix]
    if version:
        segments.append(version)
    segments += [env, tenant, site, device, stream, name]
    return "/".join(segments)


def build_captia_subscribe_pattern(
    *,
    env: str = "+",
    tenant: str = "+",
    site: str = "+",
    device: str = "+",
    stream: str = "+",
    name: str = "#",
    prefix: str = "captia",
    version: Optional[str] = None,
) -> str:
    """Build MQTT subscribe pattern for CAPTIA namespace with wildcards."""
    segments = [prefix]
    if version:
        segments.append(version)
    segments += [env, tenant, site, device, stream, name]
    return "/".join(segments)
