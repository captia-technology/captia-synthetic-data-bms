"""Variable catalog loader — reads variables.yaml for a domain.

Single source of truth for metric_kind, counter_wire, and variable metadata.
Each domain has a config/domains/<domain_id>/variables.yaml that declares
all variables with their explicit metric_kind for downsampling.

Usage:
    from synthetic_generator.core.variable_catalog import load_variable_catalog

    catalog = load_variable_catalog(domain_config_dir / "variables.yaml")
    variables = catalog.get_variables("classroom")
    # Returns list[VariableDef] with metric_kind populated
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

from .models import (
    CounterWire,
    DataType,
    MetricKind,
    PointType,
    VariableDef,
)

LOG = logging.getLogger("synthetic_generator.core.variable_catalog")

# Map YAML string values → enums
_DATA_TYPE_MAP = {
    "float": DataType.FLOAT,
    "integer": DataType.INTEGER,
    "boolean": DataType.BOOLEAN,
    "string": DataType.STRING,
    "enum": DataType.ENUM,
}

_POINT_TYPE_MAP = {
    "sensor": PointType.SENSOR,
    "actuator": PointType.ACTUATOR,
    "setpoint": PointType.SETPOINT,
    "calculated": PointType.CALCULATED,
}

_METRIC_KIND_MAP = {
    "analog_gauge": MetricKind.ANALOG_GAUGE,
    "bool_presence": MetricKind.BOOL_PRESENCE,
    "bool_state": MetricKind.BOOL_STATE,
    "setpoint_step": MetricKind.SETPOINT_STEP,
    "counter": MetricKind.COUNTER,
    "skip": MetricKind.SKIP,
}

_COUNTER_WIRE_MAP = {
    "cumulative_monotonic": CounterWire.CUMULATIVE_MONOTONIC,
    "delta_already": CounterWire.DELTA_ALREADY,
}


@dataclass
class VariableCatalog:
    """Parsed variable catalog for one domain.

    Attributes:
        asset_type_vars: mapping of asset_type → list of VariableDef
        source_path: path to the YAML file that was loaded
    """
    asset_type_vars: dict[str, list[VariableDef]] = field(default_factory=dict)
    source_path: Optional[Path] = None

    def get_variables(self, asset_type: str) -> list[VariableDef]:
        """Get variables for an asset type. Returns empty list if unknown."""
        return list(self.asset_type_vars.get(asset_type, []))

    def get_variables_by_metric_kind(
        self, asset_type: str, metric_kind: MetricKind
    ) -> list[VariableDef]:
        """Get variables of a specific metric_kind for an asset type."""
        return [
            v for v in self.get_variables(asset_type)
            if v.metric_kind == metric_kind
        ]

    def list_asset_types(self) -> list[str]:
        """List all asset types in this catalog."""
        return list(self.asset_type_vars.keys())

    def build_allowlists(self) -> dict[str, list[str]]:
        """Build variable allowlists grouped by metric_kind.

        Returns dict like:
            {"analog_gauge": ["temperature", "humidity", ...],
             "bool_presence": ["presence_pir", ...], ...}

        Used to generate Flux task variable filters.
        """
        result: dict[str, list[str]] = {}
        for variables in self.asset_type_vars.values():
            for v in variables:
                key = v.metric_kind.value
                if key not in result:
                    result[key] = []
                if v.name not in result[key]:
                    result[key].append(v.name)
        return result


def load_variable_catalog(yaml_path: Path) -> VariableCatalog:
    """Load a variables.yaml and return a VariableCatalog.

    Args:
        yaml_path: Path to variables.yaml file

    Returns:
        VariableCatalog with parsed VariableDef instances

    Raises:
        FileNotFoundError: if yaml_path does not exist
        ValueError: if YAML is malformed or has invalid enum values
    """
    if not yaml_path.exists():
        raise FileNotFoundError(f"Variable catalog not found: {yaml_path}")

    with open(yaml_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if not raw or "asset_types" not in raw:
        raise ValueError(f"Invalid variables.yaml — missing 'asset_types' key: {yaml_path}")

    catalog = VariableCatalog(source_path=yaml_path)

    for asset_type, asset_cfg in raw["asset_types"].items():
        variables_raw = asset_cfg.get("variables", [])
        variables: list[VariableDef] = []

        for idx, var_raw in enumerate(variables_raw):
            try:
                vdef = _parse_variable_def(var_raw)
                variables.append(vdef)
            except (KeyError, ValueError) as exc:
                raise ValueError(
                    f"Error parsing variable #{idx} ({var_raw.get('name', '?')}) "
                    f"in asset_type '{asset_type}' from {yaml_path}: {exc}"
                ) from exc

        catalog.asset_type_vars[asset_type] = variables
        LOG.debug(
            "Loaded %d variables for asset_type '%s' from %s",
            len(variables), asset_type, yaml_path,
        )

    LOG.info(
        "Variable catalog loaded: %s (%d asset types, %d total variables)",
        yaml_path.name,
        len(catalog.asset_type_vars),
        sum(len(v) for v in catalog.asset_type_vars.values()),
    )
    return catalog


def _parse_variable_def(raw: dict[str, Any]) -> VariableDef:
    """Parse a single variable dict from YAML into a VariableDef."""
    name = raw["name"]

    # Required: metric_kind
    metric_kind_str = raw.get("metric_kind")
    if metric_kind_str is None:
        raise ValueError(f"Variable '{name}' is missing required field 'metric_kind'")
    if metric_kind_str not in _METRIC_KIND_MAP:
        raise ValueError(
            f"Variable '{name}' has invalid metric_kind '{metric_kind_str}'. "
            f"Valid: {list(_METRIC_KIND_MAP.keys())}"
        )
    metric_kind = _METRIC_KIND_MAP[metric_kind_str]

    # Optional: counter_wire (required if metric_kind == counter)
    counter_wire_str = raw.get("counter_wire")
    counter_wire = None
    if counter_wire_str:
        if counter_wire_str not in _COUNTER_WIRE_MAP:
            raise ValueError(
                f"Variable '{name}' has invalid counter_wire '{counter_wire_str}'. "
                f"Valid: {list(_COUNTER_WIRE_MAP.keys())}"
            )
        counter_wire = _COUNTER_WIRE_MAP[counter_wire_str]
    elif metric_kind == MetricKind.COUNTER:
        raise ValueError(
            f"Variable '{name}' has metric_kind=counter but missing 'counter_wire'. "
            f"Must specify: cumulative_monotonic or delta_already"
        )

    # data_type
    data_type_str = raw.get("data_type", "float")
    data_type = _DATA_TYPE_MAP.get(data_type_str)
    if data_type is None:
        raise ValueError(f"Variable '{name}' has invalid data_type '{data_type_str}'")

    # point_type
    point_type_str = raw.get("point_type", "sensor")
    point_type = _POINT_TYPE_MAP.get(point_type_str)
    if point_type is None:
        raise ValueError(f"Variable '{name}' has invalid point_type '{point_type_str}'")

    # ranges
    range_val = raw.get("range")
    expected_range_hard = None
    if range_val and isinstance(range_val, list) and len(range_val) == 2:
        expected_range_hard = (float(range_val[0]), float(range_val[1]))

    # Build metadata from extra fields
    metadata: dict[str, Any] = {}
    if "enum_values" in raw:
        metadata["enum_values"] = raw["enum_values"]
    if counter_wire_str:
        metadata["counter_wire"] = counter_wire_str
    # Preserve monotonic flag for backward compat
    if metric_kind == MetricKind.COUNTER and counter_wire == CounterWire.CUMULATIVE_MONOTONIC:
        metadata["monotonic"] = True

    return VariableDef(
        name=name,
        data_type=data_type,
        unit=raw.get("unit", ""),
        point_type=point_type,
        category=raw.get("category", ""),
        expected_range_hard=expected_range_hard,
        is_optional=raw.get("optional", False),
        metric_kind=metric_kind,
        counter_wire=counter_wire,
        metadata=metadata if metadata else {},
    )


def find_variables_yaml(domain_config_dir: Path) -> Optional[Path]:
    """Find variables.yaml in a domain config directory.

    Checks for:
        1. <domain_config_dir>/variables.yaml
        2. <domain_config_dir>/variables.yml

    Returns:
        Path to the file, or None if not found
    """
    for suffix in ("yaml", "yml"):
        candidate = domain_config_dir / f"variables.{suffix}"
        if candidate.exists():
            return candidate
    return None
