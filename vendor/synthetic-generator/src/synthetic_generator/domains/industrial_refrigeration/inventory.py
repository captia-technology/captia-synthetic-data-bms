"""Inventory builder for Industrial Refrigeration domain.

Creates asset and variable inventory from configuration.
Reads variable definitions (including metric_kind) from variables.yaml
when available, falling back to hardcoded defaults.
"""
from __future__ import annotations

import logging
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
from ...core.variable_catalog import VariableCatalog, find_variables_yaml, load_variable_catalog

LOG = logging.getLogger("synthetic_generator.domains.industrial_refrigeration.inventory")


def build_refrigeration_inventory(
    project_cfg: dict[str, Any],
    domain_cfg: dict[str, Any]
) -> Inventory:
    """Build Industrial Refrigeration inventory from configuration.

    Args:
        project_cfg: Project-level configuration
        domain_cfg: Domain-specific configuration

    Returns:
        Inventory containing all refrigeration assets and variables
    """
    # Try loading variable catalog from YAML
    catalog = _load_catalog(domain_cfg)

    assets = []

    # Get configuration
    inv_cfg = domain_cfg.get("inventory", {})
    assets_cfg = inv_cfg.get("assets", [])

    # Chamber assets
    chamber_ids = []
    for asset_def in assets_cfg:
        if asset_def.get("asset_type") == "cold_room":
            # Handle toggle group for chambers
            if "asset_ids" in asset_def:
                chamber_ids.extend(asset_def["asset_ids"])
            elif "asset_id" in asset_def:
                chamber_ids.append(asset_def["asset_id"])

    # Default 10 chambers if not specified
    if not chamber_ids:
        chamber_ids = [f"CAMARA{i}" for i in range(1, 11)]

    for chamber_id in chamber_ids:
        cold_room_vars = (
            catalog.get_variables("cold_room") if catalog else None
        ) or _build_chamber_variables()
        assets.append(Asset(
            asset_id=chamber_id,
            asset_type="cold_room",
            variables=tuple(cold_room_vars),
        ))

    # Compressor rack
    compressor_vars = (
        catalog.get_variables("compressor_rack") if catalog else None
    ) or _build_compressor_variables()
    assets.append(Asset(
        asset_id="COMPRESORES_GRASSO",
        asset_type="compressor_rack",
        variables=tuple(compressor_vars),
    ))

    # Condenser
    condenser_vars = (
        catalog.get_variables("condenser") if catalog else None
    ) or _build_condenser_variables()
    assets.append(Asset(
        asset_id="CONDENSADOR_GRASSO",
        asset_type="condenser",
        variables=tuple(condenser_vars),
    ))

    # Separators — both use "separator" asset_type in catalog
    separator_vars = (
        catalog.get_variables("separator") if catalog else None
    ) or _build_separator_variables()
    assets.append(Asset(
        asset_id="SEPARADOR_ALTA_GRASSO",
        asset_type="separator_high",
        variables=tuple(separator_vars),
    ))

    assets.append(Asset(
        asset_id="SEPARADOR_BAJA_GRASSO",
        asset_type="separator_low",
        variables=tuple(separator_vars),
    ))

    # Pumps
    pump_vars = (
        catalog.get_variables("separator_pumps") if catalog else None
    ) or _build_pump_variables()
    assets.append(Asset(
        asset_id="BOMBAS_SEPARADOR_GRASSO",
        asset_type="separator_pumps",
        variables=tuple(pump_vars),
    ))

    # Energy meter
    energy_vars = (
        catalog.get_variables("power_meter") if catalog else None
    ) or _build_energy_variables()
    assets.append(Asset(
        asset_id="ENERGIAS_GRASSO",
        asset_type="power_meter",
        variables=tuple(energy_vars),
    ))

    # Weather station
    meteo_vars = (
        catalog.get_variables("weather") if catalog else None
    ) or _build_meteo_variables()
    assets.append(Asset(
        asset_id="METEO",
        asset_type="weather",
        variables=tuple(meteo_vars),
    ))

    return Inventory(
        domain_id="industrial_refrigeration",
        assets=assets,
        metadata={
            "n_chambers": len(chamber_ids),
            "site_id": project_cfg.get("site_id", "default")
        }
    )


def _load_catalog(domain_cfg: dict[str, Any]) -> VariableCatalog | None:
    """Try to load variable catalog from variables.yaml."""
    config_dir = _resolve_config_dir(domain_cfg)
    if config_dir is None:
        return None
    yaml_path = find_variables_yaml(config_dir)
    if yaml_path is None:
        return None
    try:
        catalog = load_variable_catalog(yaml_path)
        LOG.info("Loaded variable catalog from %s", yaml_path)
        return catalog
    except (ValueError, FileNotFoundError) as exc:
        LOG.warning("Failed to load variables.yaml: %s", exc)
        return None


def _resolve_config_dir(domain_cfg: dict[str, Any]) -> Path | None:
    """Resolve the config directory for this domain."""
    config_dir = domain_cfg.get("_config_dir")
    if config_dir:
        return Path(config_dir)

    this_file = Path(__file__).resolve()
    repo_root = this_file
    for _ in range(10):
        repo_root = repo_root.parent
        candidate = repo_root / "config" / "domains" / "industrial_refrigeration"
        if candidate.is_dir():
            return candidate
    return None


def _build_chamber_variables() -> list[VariableDef]:
    """Build variable definitions for a cold chamber (fallback)."""
    return [
        VariableDef(
            name="temperature",
            data_type=DataType.FLOAT,
            unit="°C",
            point_type=PointType.SENSOR,
            category="ENVIRONMENTAL",
            expected_range_soft=(-30, 15),
            expected_range_hard=(-40, 30),
            metric_kind=MetricKind.ANALOG_GAUGE,
        ),
        VariableDef(
            name="temperature_setpoint",
            data_type=DataType.FLOAT,
            unit="°C",
            point_type=PointType.SETPOINT,
            category="HVAC",
            expected_range_soft=(-25, 10),
            expected_range_hard=(-40, 20),
            metric_kind=MetricKind.SETPOINT_STEP,
        ),
        VariableDef(
            name="evap1_cooling_cmd",
            data_type=DataType.BOOLEAN,
            unit="",
            point_type=PointType.ACTUATOR,
            category="HVAC",
            metric_kind=MetricKind.BOOL_STATE,
        ),
        VariableDef(
            name="evap1_defrost_cmd",
            data_type=DataType.BOOLEAN,
            unit="",
            point_type=PointType.ACTUATOR,
            category="HVAC",
            metric_kind=MetricKind.BOOL_STATE,
        ),
        VariableDef(
            name="evap2_cooling_cmd",
            data_type=DataType.BOOLEAN,
            unit="",
            point_type=PointType.ACTUATOR,
            category="HVAC",
            is_optional=True,
            metric_kind=MetricKind.BOOL_STATE,
        ),
        VariableDef(
            name="evap2_defrost_cmd",
            data_type=DataType.BOOLEAN,
            unit="",
            point_type=PointType.ACTUATOR,
            category="HVAC",
            is_optional=True,
            metric_kind=MetricKind.BOOL_STATE,
        ),
    ]


def _build_compressor_variables() -> list[VariableDef]:
    """Build variable definitions for compressor rack (fallback)."""
    variables = [
        VariableDef(
            name="rack_suction_pressure",
            data_type=DataType.FLOAT,
            unit="bar",
            point_type=PointType.SENSOR,
            category="HVAC",
            expected_range_soft=(0.2, 5.0),
            expected_range_hard=(0.0, 10.0),
            metric_kind=MetricKind.ANALOG_GAUGE,
        ),
        VariableDef(
            name="rack_discharge_pressure",
            data_type=DataType.FLOAT,
            unit="bar",
            point_type=PointType.SENSOR,
            category="HVAC",
            expected_range_soft=(1.0, 35.0),
            expected_range_hard=(0.0, 60.0),
            metric_kind=MetricKind.ANALOG_GAUGE,
        ),
        VariableDef(
            name="rack_suction_temperature",
            data_type=DataType.FLOAT,
            unit="°C",
            point_type=PointType.SENSOR,
            category="HVAC",
            expected_range_soft=(-45, 10),
            expected_range_hard=(-60, 30),
            metric_kind=MetricKind.ANALOG_GAUGE,
        ),
        VariableDef(
            name="rack_discharge_temperature",
            data_type=DataType.FLOAT,
            unit="°C",
            point_type=PointType.SENSOR,
            category="HVAC",
            expected_range_soft=(-20, 80),
            expected_range_hard=(-40, 120),
            metric_kind=MetricKind.ANALOG_GAUGE,
        ),
    ]

    # Add individual compressor status
    for cid in ["compressor_2_status", "compressor_3_status", "compressor_4_status",
                "compressor_5_status", "compressor_6_status", "compressor_8_status"]:
        variables.append(VariableDef(
            name=cid,
            data_type=DataType.BOOLEAN,
            unit="",
            point_type=PointType.ACTUATOR,
            category="HVAC",
            metric_kind=MetricKind.BOOL_STATE,
        ))

    return variables


def _build_condenser_variables() -> list[VariableDef]:
    """Build variable definitions for condenser (fallback)."""
    return [
        VariableDef(
            name="condenser_discharge_pressure",
            data_type=DataType.FLOAT,
            unit="bar",
            point_type=PointType.SENSOR,
            category="HVAC",
            expected_range_soft=(5, 40),
            expected_range_hard=(0, 70),
            metric_kind=MetricKind.ANALOG_GAUGE,
        ),
        VariableDef(
            name="condenser_discharge_temperature",
            data_type=DataType.FLOAT,
            unit="°C",
            point_type=PointType.SENSOR,
            category="HVAC",
            expected_range_soft=(-10, 60),
            expected_range_hard=(-30, 90),
            metric_kind=MetricKind.ANALOG_GAUGE,
        ),
        VariableDef(
            name="condenser_vfd_frequency",
            data_type=DataType.FLOAT,
            unit="Hz",
            point_type=PointType.ACTUATOR,
            category="HVAC",
            expected_range_soft=(0, 50),
            expected_range_hard=(0, 60),
            metric_kind=MetricKind.ANALOG_GAUGE,
        ),
    ]


def _build_separator_variables() -> list[VariableDef]:
    """Build variable definitions for separator (fallback)."""
    return [
        VariableDef(
            name="separator_level",
            data_type=DataType.FLOAT,
            unit="%",
            point_type=PointType.SENSOR,
            category="HVAC",
            expected_range_soft=(0, 100),
            expected_range_hard=(0, 110),
            metric_kind=MetricKind.ANALOG_GAUGE,
        ),
        VariableDef(
            name="separator_pressure",
            data_type=DataType.FLOAT,
            unit="bar",
            point_type=PointType.SENSOR,
            category="HVAC",
            expected_range_soft=(0.2, 40),
            expected_range_hard=(0, 70),
            metric_kind=MetricKind.ANALOG_GAUGE,
        ),
        VariableDef(
            name="separator_temperature",
            data_type=DataType.FLOAT,
            unit="°C",
            point_type=PointType.SENSOR,
            category="HVAC",
            expected_range_soft=(-50, 80),
            expected_range_hard=(-80, 120),
            metric_kind=MetricKind.ANALOG_GAUGE,
        ),
        VariableDef(
            name="dp_pump_b1",
            data_type=DataType.FLOAT,
            unit="bar",
            point_type=PointType.SENSOR,
            category="HVAC",
            expected_range_soft=(0, 5),
            expected_range_hard=(0, 10),
            metric_kind=MetricKind.ANALOG_GAUGE,
        ),
        VariableDef(
            name="dp_pump_b2",
            data_type=DataType.FLOAT,
            unit="bar",
            point_type=PointType.SENSOR,
            category="HVAC",
            expected_range_soft=(0, 5),
            expected_range_hard=(0, 10),
            metric_kind=MetricKind.ANALOG_GAUGE,
        ),
    ]


def _build_pump_variables() -> list[VariableDef]:
    """Build variable definitions for separator pumps (fallback)."""
    return [
        VariableDef(
            name="pump_b1_high_status",
            data_type=DataType.BOOLEAN,
            unit="",
            point_type=PointType.ACTUATOR,
            category="HVAC",
            metric_kind=MetricKind.BOOL_STATE,
        ),
        VariableDef(
            name="pump_b1_low_status",
            data_type=DataType.BOOLEAN,
            unit="",
            point_type=PointType.ACTUATOR,
            category="HVAC",
            metric_kind=MetricKind.BOOL_STATE,
        ),
        VariableDef(
            name="pump_b2_high_status",
            data_type=DataType.BOOLEAN,
            unit="",
            point_type=PointType.ACTUATOR,
            category="HVAC",
            metric_kind=MetricKind.BOOL_STATE,
        ),
        VariableDef(
            name="pump_b2_low_status",
            data_type=DataType.BOOLEAN,
            unit="",
            point_type=PointType.ACTUATOR,
            category="HVAC",
            metric_kind=MetricKind.BOOL_STATE,
        ),
    ]


def _build_energy_variables() -> list[VariableDef]:
    """Build variable definitions for energy meter (fallback)."""
    return [
        VariableDef(
            name="power_active_total",
            data_type=DataType.FLOAT,
            unit="kW",
            point_type=PointType.SENSOR,
            category="ENERGY",
            expected_range_soft=(0, 500),
            expected_range_hard=(0, 2000),
            metric_kind=MetricKind.ANALOG_GAUGE,
        ),
        VariableDef(
            name="power_apparent_total",
            data_type=DataType.FLOAT,
            unit="kVA",
            point_type=PointType.SENSOR,
            category="ENERGY",
            expected_range_soft=(0, 800),
            expected_range_hard=(0, 4000),
            metric_kind=MetricKind.ANALOG_GAUGE,
        ),
        VariableDef(
            name="power_factor",
            data_type=DataType.FLOAT,
            unit="",
            point_type=PointType.SENSOR,
            category="ENERGY",
            expected_range_soft=(0.4, 1.0),
            expected_range_hard=(0.0, 1.0),
            metric_kind=MetricKind.ANALOG_GAUGE,
        ),
        VariableDef(
            name="energy_active",
            data_type=DataType.FLOAT,
            unit="kWh",
            point_type=PointType.SENSOR,
            category="ENERGY",
            metric_kind=MetricKind.COUNTER,
            counter_wire=CounterWire.CUMULATIVE_MONOTONIC,
            metadata={"monotonic": True},
        ),
        VariableDef(
            name="power_active_phase_a",
            data_type=DataType.FLOAT,
            unit="kW",
            point_type=PointType.SENSOR,
            category="ENERGY",
            expected_range_hard=(0, 1000),
            metric_kind=MetricKind.ANALOG_GAUGE,
        ),
        VariableDef(
            name="power_active_phase_b",
            data_type=DataType.FLOAT,
            unit="kW",
            point_type=PointType.SENSOR,
            category="ENERGY",
            expected_range_hard=(0, 1000),
            metric_kind=MetricKind.ANALOG_GAUGE,
        ),
        VariableDef(
            name="power_active_phase_c",
            data_type=DataType.FLOAT,
            unit="kW",
            point_type=PointType.SENSOR,
            category="ENERGY",
            expected_range_hard=(0, 1000),
            metric_kind=MetricKind.ANALOG_GAUGE,
        ),
    ]


def _build_meteo_variables() -> list[VariableDef]:
    """Build variable definitions for weather station (fallback)."""
    return [
        VariableDef(
            name="outdoor_temperature_2m",
            data_type=DataType.FLOAT,
            unit="°C",
            point_type=PointType.SENSOR,
            category="EXTERNAL",
            expected_range_hard=(-10, 45),
            metric_kind=MetricKind.ANALOG_GAUGE,
        ),
        VariableDef(
            name="outdoor_relative_humidity_2m",
            data_type=DataType.FLOAT,
            unit="%",
            point_type=PointType.SENSOR,
            category="EXTERNAL",
            expected_range_hard=(0, 100),
            metric_kind=MetricKind.ANALOG_GAUGE,
        ),
        VariableDef(
            name="outdoor_precipitation",
            data_type=DataType.FLOAT,
            unit="mm",
            point_type=PointType.SENSOR,
            category="EXTERNAL",
            expected_range_hard=(0, 200),
            metric_kind=MetricKind.ANALOG_GAUGE,
        ),
        VariableDef(
            name="outdoor_wind_speed_10m",
            data_type=DataType.FLOAT,
            unit="m/s",
            point_type=PointType.SENSOR,
            category="EXTERNAL",
            expected_range_hard=(0, 50),
            metric_kind=MetricKind.ANALOG_GAUGE,
        ),
        VariableDef(
            name="outdoor_wind_direction_10m",
            data_type=DataType.FLOAT,
            unit="deg",
            point_type=PointType.SENSOR,
            category="EXTERNAL",
            expected_range_hard=(0, 360),
            metric_kind=MetricKind.ANALOG_GAUGE,
        ),
    ]
