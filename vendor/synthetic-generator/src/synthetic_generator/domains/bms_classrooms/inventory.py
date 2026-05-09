"""Inventory builder for BMS Classrooms domain.

Creates asset and variable inventory from configuration.
Reads variable definitions (including metric_kind) from variables.yaml
when available, falling back to hardcoded defaults.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from ...core.models import (
    Asset,
    CounterWire,
    DataType,
    Inventory,
    MetricKind,
    PointType,
    VariableDef,
)
from ...core.variable_catalog import find_variables_yaml, load_variable_catalog

LOG = logging.getLogger("synthetic_generator.domains.bms_classrooms.inventory")


def build_bms_inventory(
    project_cfg: dict[str, Any],
    domain_cfg: dict[str, Any]
) -> Inventory:
    """Build BMS Classrooms inventory from configuration.

    Args:
        project_cfg: Project-level configuration
        domain_cfg: Domain-specific configuration

    Returns:
        Inventory containing all classroom assets and variables
    """
    n_aulas = int(os.environ.get("N_AULAS", domain_cfg.get("n_aulas", 70)))

    # Try loading from variables.yaml (includes metric_kind)
    classroom_variables = _load_variables_from_catalog(domain_cfg)
    if classroom_variables is None:
        LOG.info("No variables.yaml found, using hardcoded variable definitions")
        classroom_variables = _build_classroom_variables()

    # Create assets for each classroom
    assets = []
    for a in range(1, n_aulas + 1):
        asset_id = f"AULA{a:02d}"
        asset = Asset(
            asset_id=asset_id,
            asset_type="classroom",
            variables=tuple(classroom_variables),
            metadata={"index": a}
        )
        assets.append(asset)

    return Inventory(
        domain_id="bms_classrooms",
        assets=assets,
        metadata={
            "n_aulas": n_aulas,
            "site_id": project_cfg.get("site_id", "default")
        }
    )


def _load_variables_from_catalog(
    domain_cfg: dict[str, Any],
) -> list[VariableDef] | None:
    """Try to load variables from variables.yaml catalog.

    Searches for variables.yaml relative to the domain config path.
    Returns None if not found.
    """
    # Resolve domain config directory from the config_path if available
    # The variables.yaml lives alongside domain.yaml
    config_dir = _resolve_config_dir(domain_cfg)
    if config_dir is None:
        return None

    yaml_path = find_variables_yaml(config_dir)
    if yaml_path is None:
        return None

    try:
        catalog = load_variable_catalog(yaml_path)
        variables = catalog.get_variables("classroom")
        if variables:
            LOG.info(
                "Loaded %d variables from %s (with metric_kind)",
                len(variables), yaml_path,
            )
            return variables
        LOG.warning("variables.yaml found but no 'classroom' asset_type defined")
        return None
    except (ValueError, FileNotFoundError) as exc:
        LOG.warning("Failed to load variables.yaml: %s", exc)
        return None


def _resolve_config_dir(domain_cfg: dict[str, Any]) -> Path | None:
    """Resolve the config directory for this domain.

    Tries multiple strategies:
    1. Explicit _config_dir key (set by runner)
    2. Relative to known config layout
    """
    # Strategy 1: explicit key set by runner/plugin
    config_dir = domain_cfg.get("_config_dir")
    if config_dir:
        return Path(config_dir)

    # Strategy 2: walk up from this file to find config/domains/bms_classrooms
    this_file = Path(__file__).resolve()
    repo_root = this_file
    for _ in range(10):
        repo_root = repo_root.parent
        candidate = repo_root / "config" / "domains" / "bms_classrooms"
        if candidate.is_dir():
            return candidate

    return None


def _build_classroom_variables() -> list[VariableDef]:
    """Build standard variable definitions for a classroom (fallback)."""
    return [
        # Sensors
        VariableDef(
            name="temperature",
            data_type=DataType.FLOAT,
            unit="°C",
            point_type=PointType.SENSOR,
            category="ENVIRONMENTAL",
            expected_range_soft=(15.0, 30.0),
            expected_range_hard=(10.0, 35.0),
            metric_kind=MetricKind.ANALOG_GAUGE,
            metadata={"punto_id": "LG-048591.temperature"}
        ),
        VariableDef(
            name="humidity",
            data_type=DataType.FLOAT,
            unit="%RH",
            point_type=PointType.SENSOR,
            category="ENVIRONMENTAL",
            expected_range_soft=(30.0, 70.0),
            expected_range_hard=(10.0, 90.0),
            metric_kind=MetricKind.ANALOG_GAUGE,
            metadata={"punto_id": "LG-048591.humidity"}
        ),
        VariableDef(
            name="co2",
            data_type=DataType.FLOAT,
            unit="ppm",
            point_type=PointType.SENSOR,
            category="ENVIRONMENTAL",
            expected_range_soft=(400.0, 1500.0),
            expected_range_hard=(400.0, 2200.0),
            metric_kind=MetricKind.ANALOG_GAUGE,
            metadata={"punto_id": "LG-048591.co2"}
        ),
        VariableDef(
            name="iaq_index",
            data_type=DataType.FLOAT,
            unit="index",
            point_type=PointType.CALCULATED,
            category="ENVIRONMENTAL",
            expected_range_soft=(0.0, 300.0),
            expected_range_hard=(0.0, 500.0),
            metric_kind=MetricKind.ANALOG_GAUGE,
            metadata={"punto_id": "LG-048591.iaq_index"}
        ),
        VariableDef(
            name="noise",
            data_type=DataType.FLOAT,
            unit="dB(A)",
            point_type=PointType.SENSOR,
            category="ENVIRONMENTAL",
            expected_range_soft=(30.0, 75.0),
            expected_range_hard=(25.0, 90.0),
            metric_kind=MetricKind.ANALOG_GAUGE,
            metadata={"punto_id": "LG-048591.noise"}
        ),
        VariableDef(
            name="illuminance",
            data_type=DataType.FLOAT,
            unit="lux",
            point_type=PointType.SENSOR,
            category="ENVIRONMENTAL",
            expected_range_soft=(100.0, 1000.0),
            expected_range_hard=(0.0, 2500.0),
            metric_kind=MetricKind.ANALOG_GAUGE,
            metadata={"punto_id": "LG-048591.illuminance"}
        ),
        VariableDef(
            name="occupancy",
            data_type=DataType.INTEGER,
            unit="persons",
            point_type=PointType.SENSOR,
            category="OCCUPANCY",
            expected_range_soft=(0.0, 50.0),
            expected_range_hard=(0.0, 100.0),
            metric_kind=MetricKind.ANALOG_GAUGE,
            metadata={"punto_id": "LG-048591.occupancy"}
        ),
        VariableDef(
            name="presence_pir",
            data_type=DataType.BOOLEAN,
            unit="bool",
            point_type=PointType.SENSOR,
            category="OCCUPANCY",
            metric_kind=MetricKind.BOOL_PRESENCE,
            metadata={"punto_id": "LG-048820.presence_pir"}
        ),
        # Environment sensors
        VariableDef(
            name="outdoor_temp",
            data_type=DataType.FLOAT,
            unit="°C",
            point_type=PointType.SENSOR,
            category="EXTERNAL",
            expected_range_soft=(-5.0, 40.0),
            expected_range_hard=(-10.0, 45.0),
            metric_kind=MetricKind.ANALOG_GAUGE,
            metadata={"punto_id": "ENV.outdoor_temp"}
        ),
        VariableDef(
            name="daylight_lux",
            data_type=DataType.FLOAT,
            unit="lux",
            point_type=PointType.SENSOR,
            category="EXTERNAL",
            expected_range_soft=(0.0, 800.0),
            expected_range_hard=(0.0, 1000.0),
            metric_kind=MetricKind.ANALOG_GAUGE,
            metadata={"punto_id": "ENV.daylight_lux"}
        ),
        # Actuators
        VariableDef(
            name="thermostat_setpoint",
            data_type=DataType.FLOAT,
            unit="°C",
            point_type=PointType.SETPOINT,
            category="HVAC",
            expected_range_soft=(16.0, 26.0),
            expected_range_hard=(14.0, 30.0),
            metric_kind=MetricKind.SETPOINT_STEP,
            metadata={"punto_id": "LG-LN4691.thermostat_setpoint"}
        ),
        VariableDef(
            name="hvac_mode",
            data_type=DataType.ENUM,
            unit="enum",
            point_type=PointType.ACTUATOR,
            category="HVAC",
            metric_kind=MetricKind.SETPOINT_STEP,
            metadata={"punto_id": "LG-LN4691.hvac_mode", "enum_values": ["off", "heat", "cool", "auto"]}
        ),
        VariableDef(
            name="hvac_enable",
            data_type=DataType.BOOLEAN,
            unit="bool",
            point_type=PointType.ACTUATOR,
            category="HVAC",
            metric_kind=MetricKind.BOOL_STATE,
            metadata={"punto_id": "LG-LN4691.hvac_enable"}
        ),
        VariableDef(
            name="heating_valve_pos",
            data_type=DataType.FLOAT,
            unit="%",
            point_type=PointType.ACTUATOR,
            category="HVAC",
            expected_range_soft=(0.0, 100.0),
            expected_range_hard=(0.0, 100.0),
            metric_kind=MetricKind.ANALOG_GAUGE,
            metadata={"punto_id": "LG-F430-4.heating_valve_pos"}
        ),
        VariableDef(
            name="scene_mode",
            data_type=DataType.ENUM,
            unit="enum",
            point_type=PointType.ACTUATOR,
            category="CONTROL",
            metric_kind=MetricKind.SETPOINT_STEP,
            metadata={"punto_id": "LG-F420.scene_mode", "enum_values": ["out_of_hours", "class", "manual"]}
        ),
        # Relays
        VariableDef(
            name="relay_1",
            data_type=DataType.BOOLEAN,
            unit="bool",
            point_type=PointType.ACTUATOR,
            category="CONTROL",
            metric_kind=MetricKind.BOOL_STATE,
            metadata={"punto_id": "LG-BMSW1003.relay_1"}
        ),
        VariableDef(
            name="relay_2",
            data_type=DataType.BOOLEAN,
            unit="bool",
            point_type=PointType.ACTUATOR,
            category="CONTROL",
            metric_kind=MetricKind.BOOL_STATE,
            metadata={"punto_id": "LG-BMSW1003.relay_2"}
        ),
        VariableDef(
            name="relay_3",
            data_type=DataType.BOOLEAN,
            unit="bool",
            point_type=PointType.ACTUATOR,
            category="CONTROL",
            metric_kind=MetricKind.BOOL_STATE,
            metadata={"punto_id": "LG-BMSW1003.relay_3"}
        ),
        VariableDef(
            name="relay_4",
            data_type=DataType.BOOLEAN,
            unit="bool",
            point_type=PointType.ACTUATOR,
            category="CONTROL",
            metric_kind=MetricKind.BOOL_STATE,
            metadata={"punto_id": "LG-BMSW1003.relay_4"}
        ),
        # Energy
        VariableDef(
            name="power",
            data_type=DataType.FLOAT,
            unit="W",
            point_type=PointType.SENSOR,
            category="ENERGY",
            expected_range_soft=(0.0, 3000.0),
            expected_range_hard=(0.0, 6000.0),
            metric_kind=MetricKind.ANALOG_GAUGE,
            metadata={"punto_id": "LG-F520.power"}
        ),
        VariableDef(
            name="energy",
            data_type=DataType.FLOAT,
            unit="kWh",
            point_type=PointType.SENSOR,
            category="ENERGY",
            metric_kind=MetricKind.COUNTER,
            counter_wire=CounterWire.CUMULATIVE_MONOTONIC,
            metadata={"punto_id": "LG-F520.energy", "monotonic": True}
        ),
    ]
