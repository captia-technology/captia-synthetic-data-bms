"""Inventory builder for discrete manufacturing domain.

Builds configurable machines with WISE 6DI signals.
Reads variable definitions (including metric_kind) from variables.yaml
when available, falling back to hardcoded defaults.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np

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
from .state import MachineConfig

LOG = logging.getLogger("synthetic_generator.domains.discrete_manufacturing.inventory")

# Default machine definitions (can be overridden in domain config)
DEFAULT_MACHINES = {
    "M01": {"name": "Machine 01", "archetype": "CUTTING_MANUAL"},
    "M02": {"name": "Machine 02", "archetype": "CNC_MILL"},
    "M03": {"name": "Machine 03", "archetype": "PRESS_EMBUTIDORA"},
    "M04": {"name": "Machine 04", "archetype": "WELDING_ROBOT"},
    "M05": {"name": "Machine 05", "archetype": "BENDER"},
    "M06": {"name": "Machine 06", "archetype": "WRAPPER_PACKAGING"},
    "M07": {"name": "Machine 07", "archetype": "LASER_CUTTER"},
    "M08": {"name": "Machine 08", "archetype": "CUTTING_AUTO"},
}

EXTRA_MACHINES = {
    "M09": {"name": "Machine 09", "archetype": "PRESS_HYDRAULIC"},
    "M10": {"name": "Machine 10", "archetype": "PUNCH_PRESS"},
    "M11": {"name": "Machine 11", "archetype": "RIVET_LINE"},
    "M12": {"name": "Machine 12", "archetype": "VISION_INSPECTION"},
    "M13": {"name": "Machine 13", "archetype": "DEBURRING"},
}


def build_manufacturing_inventory(
    project_cfg: dict[str, Any], domain_cfg: dict[str, Any], rng: np.random.Generator
) -> tuple[Inventory, dict[str, MachineConfig]]:
    """Build inventory of manufacturing machines.

    Args:
        project_cfg: Project-level configuration
        domain_cfg: Domain-specific configuration
        rng: NumPy random generator

    Returns:
        Tuple of (Inventory, dict of MachineConfig by machine_id)
    """
    project = project_cfg.get("project", {})
    simulation = project_cfg.get("simulation", {})

    site_id = project.get("site_id", "PLANT_001")
    n_machines = simulation.get("n_machines", 8)
    n_machines = min(n_machines, 13)

    archetypes = domain_cfg.get("machine_archetypes", {})
    # Support both faraone_machines and machines keys for compatibility
    machines_cfg = domain_cfg.get("faraone_machines", domain_cfg.get("machines", DEFAULT_MACHINES))
    extra_machines_cfg = domain_cfg.get("extra_machines", EXTRA_MACHINES)

    # Try loading variable catalog from YAML
    catalog = _load_catalog(domain_cfg)

    machine_configs: dict[str, MachineConfig] = {}
    assets: list[Asset] = []

    machine_ids = list(machines_cfg.keys())[: min(n_machines, len(machines_cfg))]

    if n_machines > len(machines_cfg):
        extra_ids = list(extra_machines_cfg.keys())[: n_machines - len(machines_cfg)]
        machine_ids.extend(extra_ids)

    for machine_id in machine_ids:
        if machine_id in machines_cfg:
            machine_def = machines_cfg[machine_id]
        else:
            machine_def = extra_machines_cfg[machine_id]

        archetype_name = machine_def["archetype"]
        archetype = archetypes.get(archetype_name, {})

        ct_range = archetype.get("cycle_time_ideal_s", {"min": 30, "max": 120})
        idle_range = archetype.get("idle_power_kw", {"min": 1, "max": 3})
        run_range = archetype.get("run_power_kw", {"min": 5, "max": 20})
        vib_cfg = archetype.get("vibration", {})
        setup_cfg = archetype.get("setup_time_minutes", {"mean": 15, "std": 5})
        pm_dur_cfg = archetype.get("maintenance_pm_duration_minutes", {"mean": 60, "std": 15})

        config = MachineConfig(
            machine_id=machine_id,
            archetype=archetype_name,
            machine_name=machine_def["name"],
            pieces_per_cycle=archetype.get("pieces_per_cycle", 1),
            cycle_time_ideal_s=rng.uniform(ct_range["min"], ct_range["max"]),
            idle_power_kw=rng.uniform(idle_range["min"], idle_range["max"]),
            run_power_kw=rng.uniform(run_range["min"], run_range["max"]),
            startup_spike_factor=archetype.get("startup_spike_factor", 1.5),
            thermal_tau_minutes=archetype.get("thermal_tau_minutes", 15),
            vibration_base=vib_cfg.get("base_rms_mm_s", 1.0),
            vibration_load_gain=vib_cfg.get("load_gain", 1.5),
            vibration_wear_gain=vib_cfg.get("wear_gain", 1.0),
            fault_base_rate=archetype.get("fault_base_rate_per_hour", 0.02),
            fault_wear_gain=archetype.get("fault_wear_gain", 0.1),
            microstop_rate=archetype.get("microstop_rate_per_hour", 0.5),
            setup_time_mean=setup_cfg.get("mean", 15),
            setup_time_std=setup_cfg.get("std", 5),
            pm_interval_hours=archetype.get("maintenance_pm_interval_hours", 168),
            pm_duration_mean=pm_dur_cfg.get("mean", 60),
            pm_duration_std=pm_dur_cfg.get("std", 15),
            nominal_scrap_rate=archetype.get("nominal_scrap_rate", 0.01),
            nominal_rework_rate=archetype.get("nominal_rework_rate", 0.005),
            has_pneumatics=archetype.get("has_pneumatics", False),
            has_coolant=archetype.get("has_coolant", False),
        )

        machine_configs[machine_id] = config

        # Use catalog if available, otherwise fallback to hardcoded
        catalog_vars = catalog.get_variables("machine") if catalog else None
        if catalog_vars:
            # Filter optional vars based on machine config
            variables = _filter_optional_vars(catalog_vars, config)
        else:
            variables = _build_machine_variables(config.has_pneumatics)
        asset = Asset(
            asset_id=machine_id,
            asset_type="machine",
            variables=tuple(variables),
            metadata={
                "archetype": archetype_name,
                "name": machine_def["name"],
                "pieces_per_cycle": config.pieces_per_cycle,
                "has_pneumatics": config.has_pneumatics,
            },
        )
        assets.append(asset)

        LOG.debug(
            "Created machine %s (%s) - archetype=%s, pieces_per_cycle=%d",
            machine_id,
            machine_def["name"],
            archetype_name,
            config.pieces_per_cycle,
        )

    inventory = Inventory(
        domain_id="discrete_manufacturing",
        assets=assets,
        metadata={"site_id": site_id, "n_machines": len(machine_configs)},
    )

    LOG.info("Built inventory with %d machines", len(assets))
    return inventory, machine_configs


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
        candidate = repo_root / "config" / "domains" / "discrete_manufacturing"
        if candidate.is_dir():
            return candidate
    return None


def _filter_optional_vars(
    catalog_vars: list[VariableDef],
    config: MachineConfig,
) -> list[VariableDef]:
    """Filter optional variables based on machine config.

    E.g., air_pressure_bar is only included if has_pneumatics=True.
    """
    result = []
    for v in catalog_vars:
        if v.is_optional:
            # air_pressure_bar → needs has_pneumatics
            if v.name == "air_pressure_bar" and not config.has_pneumatics:
                continue
        result.append(v)
    return result


def _build_machine_variables(has_pneumatics: bool = False) -> list[VariableDef]:
    """Build variable definitions for a machine.

    CRITICAL: All state signals are BOOLEAN, not string.
    """
    variables = []

    # WISE 6DI (ALL BOOLEANS) — (name, dtype, unit, ptype, metric_kind, description)
    di_vars = [
        (
            "machine_state",
            DataType.BOOLEAN,
            "",
            PointType.SENSOR,
            MetricKind.BOOL_STATE,
            "Machine running state (DI1): true=RUN, false=STOP",
        ),
        ("fault_active", DataType.BOOLEAN, "", PointType.SENSOR, MetricKind.BOOL_STATE, "Fault/alarm active (DI2)"),
        ("estop_active", DataType.BOOLEAN, "", PointType.SENSOR, MetricKind.BOOL_STATE, "Emergency stop active (DI3)"),
        ("cycle_in_progress", DataType.BOOLEAN, "", PointType.SENSOR, MetricKind.BOOL_STATE, "Cycle in progress (DI4)"),
        (
            "material_present",
            DataType.BOOLEAN,
            "",
            PointType.SENSOR,
            MetricKind.BOOL_PRESENCE,
            "Material/piece present (DI5)",
        ),
        (
            "operator_present",
            DataType.BOOLEAN,
            "",
            PointType.SENSOR,
            MetricKind.BOOL_PRESENCE,
            "Operator present (DI6)",
        ),
        ("setup_active", DataType.BOOLEAN, "", PointType.SENSOR, MetricKind.BOOL_STATE, "Setup/changeover in progress"),
    ]

    production_vars = [
        (
            "cycle_count_total",
            DataType.INTEGER,
            "cycles",
            PointType.SENSOR,
            MetricKind.COUNTER,
            "Total completed cycles (monotonic)",
        ),
        (
            "good_count_total",
            DataType.INTEGER,
            "pcs",
            PointType.SENSOR,
            MetricKind.COUNTER,
            "Total good pieces (monotonic)",
        ),
        (
            "scrap_count_total",
            DataType.INTEGER,
            "pcs",
            PointType.SENSOR,
            MetricKind.COUNTER,
            "Total scrap pieces (monotonic)",
        ),
        (
            "rework_count_total",
            DataType.INTEGER,
            "pcs",
            PointType.SENSOR,
            MetricKind.COUNTER,
            "Total rework pieces (monotonic)",
        ),
        (
            "last_cycle_time_s",
            DataType.FLOAT,
            "s",
            PointType.SENSOR,
            MetricKind.ANALOG_GAUGE,
            "Duration of last completed cycle",
        ),
        (
            "ideal_cycle_time_sp",
            DataType.FLOAT,
            "s",
            PointType.SETPOINT,
            MetricKind.SETPOINT_STEP,
            "Ideal cycle time for current product",
        ),
    ]

    energy_vars = [
        (
            "power_kw",
            DataType.FLOAT,
            "kW",
            PointType.SENSOR,
            MetricKind.ANALOG_GAUGE,
            "Instantaneous power consumption",
        ),
        (
            "energy_kwh_total",
            DataType.FLOAT,
            "kWh",
            PointType.SENSOR,
            MetricKind.ANALOG_GAUGE,
            "Total energy (kWh)",
        ),
        ("voltage_v", DataType.FLOAT, "V", PointType.SENSOR, MetricKind.ANALOG_GAUGE, "Line voltage (~400V)"),
        ("power_factor", DataType.FLOAT, "", PointType.SENSOR, MetricKind.ANALOG_GAUGE, "Power factor (0.5-1.0)"),
    ]

    condition_vars = [
        ("motor_temp_c", DataType.FLOAT, "C", PointType.SENSOR, MetricKind.ANALOG_GAUGE, "Motor temperature"),
        (
            "vibration_rms_mm_s",
            DataType.FLOAT,
            "mm/s",
            PointType.SENSOR,
            MetricKind.ANALOG_GAUGE,
            "Vibration RMS velocity",
        ),
        ("load_factor", DataType.FLOAT, "", PointType.SENSOR, MetricKind.ANALOG_GAUGE, "Load factor (0-1)"),
    ]

    if has_pneumatics:
        condition_vars.append(
            (
                "air_pressure_bar",
                DataType.FLOAT,
                "bar",
                PointType.SENSOR,
                MetricKind.ANALOG_GAUGE,
                "Pneumatic supply pressure",
            )
        )

    context_vars = [
        ("product_code", DataType.STRING, "", PointType.SENSOR, MetricKind.SKIP, "Current product code"),
        ("order_id", DataType.STRING, "", PointType.SENSOR, MetricKind.SKIP, "Current production order ID"),
    ]

    quality_vars = [
        (
            "data_quality",
            DataType.STRING,
            "",
            PointType.SENSOR,
            MetricKind.SKIP,
            "Data quality: OK|MISSING|OUTLIER|STUCK|LATE",
        ),
    ]

    all_var_defs = di_vars + production_vars + energy_vars + condition_vars + context_vars + quality_vars

    for var_tuple in all_var_defs:
        name, dtype, unit, ptype, mkind = var_tuple[:5]
        description = var_tuple[5] if len(var_tuple) > 5 else ""
        # Set counter_wire for counter variables
        cwire = CounterWire.CUMULATIVE_MONOTONIC if mkind == MetricKind.COUNTER else None
        meta = {}
        if description:
            meta["description"] = description
        if cwire == CounterWire.CUMULATIVE_MONOTONIC:
            meta["monotonic"] = True
        variables.append(
            VariableDef(
                name=name,
                data_type=dtype,
                unit=unit,
                point_type=ptype,
                metric_kind=mkind,
                counter_wire=cwire,
                metadata=meta if meta else {},
            )
        )

    return variables
