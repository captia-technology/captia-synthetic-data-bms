"""Industrial Refrigeration domain plugin.

Implements the DomainPlugin interface for cold storage facilities.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Iterator, Optional

import numpy as np
import pandas as pd

from ..base import DomainPlugin
from ..registry import register_domain
from ...core.models import (
    Inventory,
    DataPoint,
    DataType,
    PointType,
    Quality,
)
from ...core.pv import build_pvn


from .inventory import build_refrigeration_inventory
from .context import build_refrigeration_context, RefrigerationContext
from .state import PlantState
from .calibration import calibrate_from_sample
from .physics.chambers import ChamberSimulator
from .physics.compressors import CompressorRackSimulator
from .physics.condenser import CondenserSimulator
from .physics.separators import SeparatorSimulator
from .physics.pumps import PumpSimulator
from .physics.energy import EnergyMeterSimulator

LOG = logging.getLogger("synthetic_generator.domains.industrial_refrigeration")


@register_domain
class IndustrialRefrigerationPlugin(DomainPlugin):
    """Domain plugin for Industrial Refrigeration (cold storage).

    Generates synthetic data for industrial refrigeration plants including:
    - Cold chambers with thermal dynamics
    - Compressor rack with staging control
    - Condenser with VFD control
    - Separators and pumps
    - Energy metering
    - Weather conditions
    """

    @property
    def domain_id(self) -> str:
        return "industrial_refrigeration"

    @property
    def description(self) -> str:
        return "Industrial refrigeration plant with cold chambers, compressor rack, and energy metering"

    @property
    def version(self) -> str:
        return "1.0.0"

    def build_inventory(
        self,
        project_cfg: dict[str, Any],
        domain_cfg: dict[str, Any]
    ) -> Inventory:
        """Build refrigeration inventory from configuration."""
        return build_refrigeration_inventory(project_cfg, domain_cfg)

    def build_context(
        self,
        time_index: pd.DatetimeIndex,
        project_cfg: dict[str, Any],
        domain_cfg: dict[str, Any],
        rng: np.random.Generator
    ) -> RefrigerationContext:
        """Build simulation context with weather and plant config."""
        return build_refrigeration_context(time_index, project_cfg, domain_cfg, rng)

    def simulate(
        self,
        time_index: pd.DatetimeIndex,
        inventory: Inventory,
        ctx: RefrigerationContext,
        rng: np.random.Generator
    ) -> Iterator[DataPoint]:
        """Generate simulated data points for the refrigeration plant.

        Args:
            time_index: Time points for simulation
            inventory: Plant inventory
            ctx: Simulation context
            rng: NumPy random generator

        Yields:
            DataPoint objects for each measurement
        """
        site_id = inventory.metadata.get("site_id", "default")
        physics_cfg = ctx.physics_cfg

        # Initialize simulators
        chamber_sim = ChamberSimulator(physics_cfg.get("cameras", {}), rng)
        compressor_sim = CompressorRackSimulator(physics_cfg.get("compressor_rack", {}), rng)
        condenser_sim = CondenserSimulator(physics_cfg.get("condenser", {}), rng)
        separator_sim = SeparatorSimulator(physics_cfg.get("separators", {}), rng)
        pump_sim = PumpSimulator(physics_cfg.get("separator_pumps", {}), rng)
        energy_sim = EnergyMeterSimulator(physics_cfg.get("energy", {}), rng)

        # Get chamber IDs from inventory
        chamber_ids = [
            a.asset_id for a in inventory.assets
            if a.asset_type == "cold_room"
        ]

        # Initialize plant state
        plant_state = PlantState()

        # Initialize chambers
        for cid in chamber_ids:
            setpoint = ctx.chamber_setpoints.get(cid, -20.0)
            plant_state.chambers[cid] = chamber_sim.init_chamber(cid, setpoint)

        # Initialize other systems
        plant_state.compressor_rack = compressor_sim.init_state()
        plant_state.condenser = condenser_sim.init_state()
        plant_state.separator_high = separator_sim.init_state("SEPARADOR_ALTA_GRASSO", is_high_side=True)
        plant_state.separator_low = separator_sim.init_state("SEPARADOR_BAJA_GRASSO", is_high_side=False)
        plant_state.pumps = pump_sim.init_state()
        plant_state.energy = energy_sim.init_state()

        dt_minutes = float((time_index[1] - time_index[0]).total_seconds() / 60)

        LOG.info("Simulating refrigeration plant with %d chambers", len(chamber_ids))

        # Simulate each timestep
        for i, ts in enumerate(time_index):
            # Get weather at this timestep
            weather = ctx.meteo.get_at(ts)
            ambient_temp = weather["outdoor_temperature_2m"]
            hour = ts.hour

            # Step chambers
            for cid in chamber_ids:
                chamber_state = plant_state.chambers[cid]
                plant_state.chambers[cid] = chamber_sim.step(
                    chamber_state, dt_minutes, ambient_temp, hour
                )

            # Calculate aggregate demand
            cooling_demand = plant_state.get_total_cooling_demand()

            # Step compressor rack
            plant_state.compressor_rack = compressor_sim.step(
                plant_state.compressor_rack,
                dt_minutes,
                cooling_demand,
                plant_state.condenser.effectiveness,
                ambient_temp
            )

            # Step condenser
            plant_state.condenser = condenser_sim.step(
                plant_state.condenser,
                dt_minutes,
                plant_state.compressor_rack.rack_discharge_pressure,
                ambient_temp
            )

            # Step separators
            system_activity = plant_state.get_system_activity()
            pump_b1_on = pump_sim.is_pump_running(plant_state.pumps, "b1")
            pump_b2_on = pump_sim.is_pump_running(plant_state.pumps, "b2")

            plant_state.separator_high = separator_sim.step(
                plant_state.separator_high,
                dt_minutes,
                system_activity,
                pump_b1_on,
                pump_b2_on,
                plant_state.compressor_rack.rack_discharge_pressure
            )

            plant_state.separator_low = separator_sim.step(
                plant_state.separator_low,
                dt_minutes,
                system_activity,
                pump_b1_on,
                pump_b2_on,
                plant_state.compressor_rack.rack_suction_pressure
            )

            # Step pumps (use low separator level for control)
            plant_state.pumps = pump_sim.step(
                plant_state.pumps,
                dt_minutes,
                plant_state.separator_low.separator_level
            )

            # Calculate power consumption
            compressor_power = compressor_sim.calculate_power(plant_state.compressor_rack)
            condenser_power = condenser_sim.calculate_power(plant_state.condenser)
            pump_power = pump_sim.calculate_power(plant_state.pumps)

            # Step energy meter
            plant_state.energy = energy_sim.step(
                plant_state.energy,
                dt_minutes,
                compressor_power,
                plant_state.condenser.condenser_vfd_frequency,
                pump_power
            )

            # Yield data points for this timestep
            timestamp = ts.to_pydatetime()

            # Chamber data points
            for cid, chamber in plant_state.chambers.items():
                yield from self._yield_chamber_points(timestamp, site_id, cid, chamber)

            # Compressor data points
            yield from self._yield_compressor_points(
                timestamp, site_id, plant_state.compressor_rack
            )

            # Condenser data points
            yield from self._yield_condenser_points(
                timestamp, site_id, plant_state.condenser
            )

            # Separator data points
            yield from self._yield_separator_points(
                timestamp, site_id, "SEPARADOR_ALTA_GRASSO", plant_state.separator_high
            )
            yield from self._yield_separator_points(
                timestamp, site_id, "SEPARADOR_BAJA_GRASSO", plant_state.separator_low
            )

            # Pump data points
            yield from self._yield_pump_points(timestamp, site_id, plant_state.pumps)

            # Energy data points
            yield from self._yield_energy_points(timestamp, site_id, plant_state.energy)

            # Weather data points
            yield from self._yield_meteo_points(timestamp, site_id, weather)

    def _yield_chamber_points(
        self,
        timestamp,
        site_id: str,
        chamber_id: str,
        state
    ) -> Iterator[DataPoint]:
        """Yield data points for a chamber."""
        yield DataPoint(
            timestamp=timestamp,
            domain_id=self.domain_id,
            site_id=site_id,
            asset_id=chamber_id,
            variable="temperature",
            value=round(state.temperature, 2),
            unit="°C",
            data_type=DataType.FLOAT,
            point_type=PointType.SENSOR,
            pvn=build_pvn(chamber_id, "temperature"),
        )
        yield DataPoint(
            timestamp=timestamp,
            domain_id=self.domain_id,
            site_id=site_id,
            asset_id=chamber_id,
            variable="temperature_setpoint",
            value=round(state.setpoint, 2),
            unit="°C",
            data_type=DataType.FLOAT,
            point_type=PointType.SETPOINT,
            pvn=build_pvn(chamber_id, "temperature_setpoint"),
        )
        yield DataPoint(
            timestamp=timestamp,
            domain_id=self.domain_id,
            site_id=site_id,
            asset_id=chamber_id,
            variable="evap1_cooling_cmd",
            value=state.evap1_cooling_cmd,
            unit="",
            data_type=DataType.BOOLEAN,
            point_type=PointType.ACTUATOR,
            pvn=build_pvn(chamber_id, "evap1_cooling_cmd"),
        )
        yield DataPoint(
            timestamp=timestamp,
            domain_id=self.domain_id,
            site_id=site_id,
            asset_id=chamber_id,
            variable="evap1_defrost_cmd",
            value=state.evap1_defrost_cmd,
            unit="",
            data_type=DataType.BOOLEAN,
            point_type=PointType.ACTUATOR,
            pvn=build_pvn(chamber_id, "evap1_defrost_cmd"),
        )
        yield DataPoint(
            timestamp=timestamp,
            domain_id=self.domain_id,
            site_id=site_id,
            asset_id=chamber_id,
            variable="evap2_cooling_cmd",
            value=state.evap2_cooling_cmd,
            unit="",
            data_type=DataType.BOOLEAN,
            point_type=PointType.ACTUATOR,
            pvn=build_pvn(chamber_id, "evap2_cooling_cmd"),
        )
        yield DataPoint(
            timestamp=timestamp,
            domain_id=self.domain_id,
            site_id=site_id,
            asset_id=chamber_id,
            variable="evap2_defrost_cmd",
            value=state.evap2_defrost_cmd,
            unit="",
            data_type=DataType.BOOLEAN,
            point_type=PointType.ACTUATOR,
            pvn=build_pvn(chamber_id, "evap2_defrost_cmd"),
        )

    def _yield_compressor_points(
        self,
        timestamp,
        site_id: str,
        state
    ) -> Iterator[DataPoint]:
        """Yield data points for compressor rack."""
        asset_id = "COMPRESORES_GRASSO"

        yield DataPoint(
            timestamp=timestamp,
            domain_id=self.domain_id,
            site_id=site_id,
            asset_id=asset_id,
            variable="rack_suction_pressure",
            value=round(state.rack_suction_pressure, 3),
            unit="bar",
            data_type=DataType.FLOAT,
            point_type=PointType.SENSOR,
            pvn=build_pvn(asset_id, "rack_suction_pressure"),
        )
        yield DataPoint(
            timestamp=timestamp,
            domain_id=self.domain_id,
            site_id=site_id,
            asset_id=asset_id,
            variable="rack_discharge_pressure",
            value=round(state.rack_discharge_pressure, 3),
            unit="bar",
            data_type=DataType.FLOAT,
            point_type=PointType.SENSOR,
            pvn=build_pvn(asset_id, "rack_discharge_pressure"),
        )
        yield DataPoint(
            timestamp=timestamp,
            domain_id=self.domain_id,
            site_id=site_id,
            asset_id=asset_id,
            variable="rack_suction_temperature",
            value=round(state.rack_suction_temperature, 2),
            unit="°C",
            data_type=DataType.FLOAT,
            point_type=PointType.SENSOR,
            pvn=build_pvn(asset_id, "rack_suction_temperature"),
        )
        yield DataPoint(
            timestamp=timestamp,
            domain_id=self.domain_id,
            site_id=site_id,
            asset_id=asset_id,
            variable="rack_discharge_temperature",
            value=round(state.rack_discharge_temperature, 2),
            unit="°C",
            data_type=DataType.FLOAT,
            point_type=PointType.SENSOR,
            pvn=build_pvn(asset_id, "rack_discharge_temperature"),
        )

        # Individual compressor status
        for comp_id, status in state.compressor_states.items():
            yield DataPoint(
                timestamp=timestamp,
                domain_id=self.domain_id,
                site_id=site_id,
                asset_id=asset_id,
                variable=comp_id,
                value=status,
                unit="",
                data_type=DataType.BOOLEAN,
                point_type=PointType.ACTUATOR,
                pvn=build_pvn(asset_id, comp_id),
            )

    def _yield_condenser_points(
        self,
        timestamp,
        site_id: str,
        state
    ) -> Iterator[DataPoint]:
        """Yield data points for condenser."""
        asset_id = "CONDENSADOR_GRASSO"

        yield DataPoint(
            timestamp=timestamp,
            domain_id=self.domain_id,
            site_id=site_id,
            asset_id=asset_id,
            variable="condenser_discharge_pressure",
            value=round(state.condenser_discharge_pressure, 3),
            unit="bar",
            data_type=DataType.FLOAT,
            point_type=PointType.SENSOR,
            pvn=build_pvn(asset_id, "condenser_discharge_pressure"),
        )
        yield DataPoint(
            timestamp=timestamp,
            domain_id=self.domain_id,
            site_id=site_id,
            asset_id=asset_id,
            variable="condenser_discharge_temperature",
            value=round(state.condenser_discharge_temperature, 2),
            unit="°C",
            data_type=DataType.FLOAT,
            point_type=PointType.SENSOR,
            pvn=build_pvn(asset_id, "condenser_discharge_temperature"),
        )
        yield DataPoint(
            timestamp=timestamp,
            domain_id=self.domain_id,
            site_id=site_id,
            asset_id=asset_id,
            variable="condenser_vfd_frequency",
            value=round(state.condenser_vfd_frequency, 1),
            unit="Hz",
            data_type=DataType.FLOAT,
            point_type=PointType.ACTUATOR,
            pvn=build_pvn(asset_id, "condenser_vfd_frequency"),
        )

    def _yield_separator_points(
        self,
        timestamp,
        site_id: str,
        asset_id: str,
        state
    ) -> Iterator[DataPoint]:
        """Yield data points for separator."""
        yield DataPoint(
            timestamp=timestamp,
            domain_id=self.domain_id,
            site_id=site_id,
            asset_id=asset_id,
            variable="separator_level",
            value=round(state.separator_level, 1),
            unit="%",
            data_type=DataType.FLOAT,
            point_type=PointType.SENSOR,
            pvn=build_pvn(asset_id, "separator_level"),
        )
        yield DataPoint(
            timestamp=timestamp,
            domain_id=self.domain_id,
            site_id=site_id,
            asset_id=asset_id,
            variable="separator_pressure",
            value=round(state.separator_pressure, 3),
            unit="bar",
            data_type=DataType.FLOAT,
            point_type=PointType.SENSOR,
            pvn=build_pvn(asset_id, "separator_pressure"),
        )
        yield DataPoint(
            timestamp=timestamp,
            domain_id=self.domain_id,
            site_id=site_id,
            asset_id=asset_id,
            variable="separator_temperature",
            value=round(state.separator_temperature, 2),
            unit="°C",
            data_type=DataType.FLOAT,
            point_type=PointType.SENSOR,
            pvn=build_pvn(asset_id, "separator_temperature"),
        )
        yield DataPoint(
            timestamp=timestamp,
            domain_id=self.domain_id,
            site_id=site_id,
            asset_id=asset_id,
            variable="dp_pump_b1",
            value=round(state.dp_pump_b1, 3),
            unit="bar",
            data_type=DataType.FLOAT,
            point_type=PointType.SENSOR,
            pvn=build_pvn(asset_id, "dp_pump_b1"),
        )
        yield DataPoint(
            timestamp=timestamp,
            domain_id=self.domain_id,
            site_id=site_id,
            asset_id=asset_id,
            variable="dp_pump_b2",
            value=round(state.dp_pump_b2, 3),
            unit="bar",
            data_type=DataType.FLOAT,
            point_type=PointType.SENSOR,
            pvn=build_pvn(asset_id, "dp_pump_b2"),
        )

    def _yield_pump_points(
        self,
        timestamp,
        site_id: str,
        state
    ) -> Iterator[DataPoint]:
        """Yield data points for pumps."""
        asset_id = "BOMBAS_SEPARADOR_GRASSO"

        yield DataPoint(
            timestamp=timestamp,
            domain_id=self.domain_id,
            site_id=site_id,
            asset_id=asset_id,
            variable="pump_b1_high_status",
            value=state.pump_b1_high_status,
            unit="",
            data_type=DataType.BOOLEAN,
            point_type=PointType.ACTUATOR,
            pvn=build_pvn(asset_id, "pump_b1_high_status"),
        )
        yield DataPoint(
            timestamp=timestamp,
            domain_id=self.domain_id,
            site_id=site_id,
            asset_id=asset_id,
            variable="pump_b1_low_status",
            value=state.pump_b1_low_status,
            unit="",
            data_type=DataType.BOOLEAN,
            point_type=PointType.ACTUATOR,
            pvn=build_pvn(asset_id, "pump_b1_low_status"),
        )
        yield DataPoint(
            timestamp=timestamp,
            domain_id=self.domain_id,
            site_id=site_id,
            asset_id=asset_id,
            variable="pump_b2_high_status",
            value=state.pump_b2_high_status,
            unit="",
            data_type=DataType.BOOLEAN,
            point_type=PointType.ACTUATOR,
            pvn=build_pvn(asset_id, "pump_b2_high_status"),
        )
        yield DataPoint(
            timestamp=timestamp,
            domain_id=self.domain_id,
            site_id=site_id,
            asset_id=asset_id,
            variable="pump_b2_low_status",
            value=state.pump_b2_low_status,
            unit="",
            data_type=DataType.BOOLEAN,
            point_type=PointType.ACTUATOR,
            pvn=build_pvn(asset_id, "pump_b2_low_status"),
        )

    def _yield_energy_points(
        self,
        timestamp,
        site_id: str,
        state
    ) -> Iterator[DataPoint]:
        """Yield data points for energy metering."""
        asset_id = "ENERGIAS_GRASSO"

        yield DataPoint(
            timestamp=timestamp,
            domain_id=self.domain_id,
            site_id=site_id,
            asset_id=asset_id,
            variable="power_active_total",
            value=state.power_active_total,
            unit="kW",
            data_type=DataType.FLOAT,
            point_type=PointType.SENSOR,
            pvn=build_pvn(asset_id, "power_active_total"),
        )
        yield DataPoint(
            timestamp=timestamp,
            domain_id=self.domain_id,
            site_id=site_id,
            asset_id=asset_id,
            variable="power_apparent_total",
            value=state.power_apparent_total,
            unit="kVA",
            data_type=DataType.FLOAT,
            point_type=PointType.SENSOR,
            pvn=build_pvn(asset_id, "power_apparent_total"),
        )
        yield DataPoint(
            timestamp=timestamp,
            domain_id=self.domain_id,
            site_id=site_id,
            asset_id=asset_id,
            variable="power_factor",
            value=state.power_factor,
            unit="",
            data_type=DataType.FLOAT,
            point_type=PointType.SENSOR,
            pvn=build_pvn(asset_id, "power_factor"),
        )
        yield DataPoint(
            timestamp=timestamp,
            domain_id=self.domain_id,
            site_id=site_id,
            asset_id=asset_id,
            variable="energy_active",
            value=state.energy_active,
            unit="kWh",
            data_type=DataType.FLOAT,
            point_type=PointType.SENSOR,
            pvn=build_pvn(asset_id, "energy_active"),
        )
        yield DataPoint(
            timestamp=timestamp,
            domain_id=self.domain_id,
            site_id=site_id,
            asset_id=asset_id,
            variable="power_active_phase_a",
            value=state.power_active_phase_a,
            unit="kW",
            data_type=DataType.FLOAT,
            point_type=PointType.SENSOR,
            pvn=build_pvn(asset_id, "power_active_phase_a"),
        )
        yield DataPoint(
            timestamp=timestamp,
            domain_id=self.domain_id,
            site_id=site_id,
            asset_id=asset_id,
            variable="power_active_phase_b",
            value=state.power_active_phase_b,
            unit="kW",
            data_type=DataType.FLOAT,
            point_type=PointType.SENSOR,
            pvn=build_pvn(asset_id, "power_active_phase_b"),
        )
        yield DataPoint(
            timestamp=timestamp,
            domain_id=self.domain_id,
            site_id=site_id,
            asset_id=asset_id,
            variable="power_active_phase_c",
            value=state.power_active_phase_c,
            unit="kW",
            data_type=DataType.FLOAT,
            point_type=PointType.SENSOR,
            pvn=build_pvn(asset_id, "power_active_phase_c"),
        )

    def _yield_meteo_points(
        self,
        timestamp,
        site_id: str,
        weather: dict[str, float]
    ) -> Iterator[DataPoint]:
        """Yield data points for weather station."""
        asset_id = "METEO"

        for var, val in weather.items():
            unit = ""
            if "temperature" in var:
                unit = "°C"
            elif "humidity" in var:
                unit = "%"
            elif "precipitation" in var:
                unit = "mm"
            elif "wind_speed" in var:
                unit = "m/s"
            elif "wind_direction" in var:
                unit = "deg"

            yield DataPoint(
                timestamp=timestamp,
                domain_id=self.domain_id,
                site_id=site_id,
                asset_id=asset_id,
                variable=var,
                value=round(val, 2),
                unit=unit,
                data_type=DataType.FLOAT,
                point_type=PointType.SENSOR,
                pvn=build_pvn(asset_id, var),
            )

    def calibrate_from_sample(
        self,
        sample_path: Path,
        output_path: Optional[Path] = None
    ) -> Optional[dict[str, Any]]:
        """Calibrate domain parameters from sample data."""
        return calibrate_from_sample(sample_path, output_path)

    def get_required_config_keys(self) -> list[str]:
        """Required configuration keys for Industrial Refrigeration."""
        return []  # All have defaults

    def validate_config(
        self,
        project_cfg: dict[str, Any],
        domain_cfg: dict[str, Any]
    ) -> list[str]:
        """Validate Industrial Refrigeration configuration."""
        errors = super().validate_config(project_cfg, domain_cfg)
        # Add domain-specific validation if needed
        return errors
