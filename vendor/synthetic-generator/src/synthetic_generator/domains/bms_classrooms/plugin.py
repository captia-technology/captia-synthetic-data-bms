"""BMS Classrooms domain plugin.

Implements the DomainPlugin interface for classroom building management systems.
"""
from __future__ import annotations

import logging
from typing import Any, Iterator

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
from ...core.pv import build_pvn, build_pvp

from .inventory import build_bms_inventory
from .context import build_bms_context, BMSClassroomsContext
from .physics import (
    sample_aula_parameters,
    generate_occupancy_count,
    derive_scene,
    thermostat_setpoint,
    hvac_mode,
    hvac_enable,
    heating_valve_position,
    light_state,
    simulate_indoor_temperature,
    simulate_co2,
    simulate_humidity,
    simulate_noise,
    simulate_illuminance,
    derive_pir_presence,
    simulate_power,
    integrate_energy_kwh,
)

LOG = logging.getLogger("synthetic_generator.domains.bms_classrooms")


@register_domain
class BMSClassroomsPlugin(DomainPlugin):
    """Domain plugin for BMS Classrooms (school building management).

    Generates synthetic data for classroom environmental monitoring
    and HVAC control systems.
    """

    @property
    def domain_id(self) -> str:
        return "bms_classrooms"

    @property
    def description(self) -> str:
        return "Building Management System for school classrooms with environmental monitoring and HVAC control"

    @property
    def version(self) -> str:
        return "1.0.0"

    def build_inventory(
        self,
        project_cfg: dict[str, Any],
        domain_cfg: dict[str, Any]
    ) -> Inventory:
        """Build classroom inventory from configuration."""
        return build_bms_inventory(project_cfg, domain_cfg)

    def build_context(
        self,
        time_index: pd.DatetimeIndex,
        project_cfg: dict[str, Any],
        domain_cfg: dict[str, Any],
        rng: np.random.Generator
    ) -> BMSClassroomsContext:
        """Build simulation context with shared environment."""
        return build_bms_context(time_index, project_cfg, domain_cfg, rng)

    def simulate(
        self,
        time_index: pd.DatetimeIndex,
        inventory: Inventory,
        ctx: BMSClassroomsContext,
        rng: np.random.Generator
    ) -> Iterator[DataPoint]:
        """Generate simulated data points for all classrooms.

        Args:
            time_index: Time points for simulation
            inventory: Classroom inventory
            ctx: Simulation context
            rng: NumPy random generator

        Yields:
            DataPoint objects for each measurement
        """
        project_cfg = ctx.physics_cfg  # Access config from context
        site_id = inventory.metadata.get("site_id", "default")

        # Get schedule parameters
        sched_cfg = ctx.schedule_cfg
        cap_mean = float(sched_cfg.get("aula_capacity_mean", 28))
        cap_std = float(sched_cfg.get("aula_capacity_std", 6))
        util_mean = float(sched_cfg.get("aula_utilization_mean", 0.75))
        util_std = float(sched_cfg.get("aula_utilization_std", 0.10))
        day_var = float(sched_cfg.get("day_to_day_variability", 0.12))

        # Get physics config
        phys = ctx.physics_cfg
        cfg_indoor = phys.get("indoor", {})
        cfg_co2 = phys.get("co2", {})
        cfg_h = phys.get("humidity", {})
        cfg_noise = phys.get("noise", {})
        cfg_light = phys.get("light", {})

        LOG.info("Simulating %d classrooms", len(inventory.assets))

        for asset in inventory.assets:
            asset_id = asset.asset_id
            aula_rng = np.random.default_rng(int(rng.integers(0, 2**31 - 1)))

            # Sample classroom parameters
            capacity, util = sample_aula_parameters(
                aula_rng, cap_mean, cap_std, util_mean, util_std
            )

            # Generate occupancy
            occ = generate_occupancy_count(
                time_index, ctx.occupancy_probability, capacity, util, day_var, aula_rng
            )

            # Generate scene and setpoint
            scene = derive_scene(time_index, occ, ctx.school_mask, aula_rng)
            setp = thermostat_setpoint(scene, cfg_indoor, aula_rng)

            # HVAC control
            mode = hvac_mode(ctx.outdoor_temp, aula_rng)
            enable0 = ((scene.values == "class") & (occ.values > 0)).astype(int)
            indoor_temp = simulate_indoor_temperature(
                time_index, ctx.outdoor_temp, occ, setp,
                pd.Series(enable0, index=time_index), cfg_indoor, aula_rng
            )
            enable = hvac_enable(indoor_temp, setp, occ, scene)

            # Re-simulate with actual enable
            indoor_temp = simulate_indoor_temperature(
                time_index, ctx.outdoor_temp, occ, setp, enable, cfg_indoor, aula_rng
            )

            valve = heating_valve_position(indoor_temp, setp, mode)
            light = light_state(occ, ctx.daylight_lux, aula_rng)

            # Indoor environment
            co2 = simulate_co2(time_index, occ, enable, cfg_co2, aula_rng)
            hum = simulate_humidity(time_index, ctx.outdoor_temp, occ, cfg_h, aula_rng)
            noi = simulate_noise(time_index, occ, cfg_noise, aula_rng)
            illum = simulate_illuminance(time_index, ctx.daylight_lux, light, cfg_light, aula_rng)
            pir = derive_pir_presence(occ, aula_rng)

            # Energy
            power = simulate_power(time_index, occ, light, enable, aula_rng)
            energy = integrate_energy_kwh(time_index, power)

            # IAQ index
            iaq = pd.Series(np.clip((co2.values - 400) / 3.2, 0, 500), index=time_index)

            # Relays
            relay_1 = light.copy()
            relay_2 = enable.copy()
            relay_3 = (valve > 5).astype(int)
            relay_4 = pd.Series((aula_rng.random(len(time_index)) < 0.0002).astype(int), index=time_index)

            # Yield data points for this classroom
            yield from self._yield_series_points(
                time_index, site_id, asset_id, "temperature", indoor_temp,
                "°C", DataType.FLOAT, PointType.SENSOR
            )
            yield from self._yield_series_points(
                time_index, site_id, asset_id, "humidity", hum,
                "%RH", DataType.FLOAT, PointType.SENSOR
            )
            yield from self._yield_series_points(
                time_index, site_id, asset_id, "co2", co2,
                "ppm", DataType.FLOAT, PointType.SENSOR
            )
            yield from self._yield_series_points(
                time_index, site_id, asset_id, "iaq_index", iaq,
                "index", DataType.FLOAT, PointType.CALCULATED
            )
            yield from self._yield_series_points(
                time_index, site_id, asset_id, "noise", noi,
                "dB(A)", DataType.FLOAT, PointType.SENSOR
            )
            yield from self._yield_series_points(
                time_index, site_id, asset_id, "illuminance", illum,
                "lux", DataType.FLOAT, PointType.SENSOR
            )
            yield from self._yield_series_points(
                time_index, site_id, asset_id, "occupancy", occ,
                "persons", DataType.INTEGER, PointType.SENSOR
            )
            yield from self._yield_series_points(
                time_index, site_id, asset_id, "presence_pir", pir,
                "bool", DataType.BOOLEAN, PointType.SENSOR
            )
            yield from self._yield_series_points(
                time_index, site_id, asset_id, "outdoor_temp", ctx.outdoor_temp,
                "°C", DataType.FLOAT, PointType.SENSOR
            )
            yield from self._yield_series_points(
                time_index, site_id, asset_id, "daylight_lux", ctx.daylight_lux,
                "lux", DataType.FLOAT, PointType.SENSOR
            )
            yield from self._yield_series_points(
                time_index, site_id, asset_id, "thermostat_setpoint", setp,
                "°C", DataType.FLOAT, PointType.SETPOINT
            )
            yield from self._yield_enum_points(
                time_index, site_id, asset_id, "hvac_mode", mode,
                {"off": 0, "heat": 1, "cool": 2, "auto": 3}
            )
            yield from self._yield_series_points(
                time_index, site_id, asset_id, "hvac_enable", enable,
                "bool", DataType.BOOLEAN, PointType.ACTUATOR
            )
            yield from self._yield_series_points(
                time_index, site_id, asset_id, "heating_valve_pos", valve,
                "%", DataType.FLOAT, PointType.ACTUATOR
            )
            yield from self._yield_enum_points(
                time_index, site_id, asset_id, "scene_mode", scene,
                {"out_of_hours": 0, "class": 1, "manual": 2}
            )
            yield from self._yield_series_points(
                time_index, site_id, asset_id, "relay_1", relay_1,
                "bool", DataType.BOOLEAN, PointType.ACTUATOR
            )
            yield from self._yield_series_points(
                time_index, site_id, asset_id, "relay_2", relay_2,
                "bool", DataType.BOOLEAN, PointType.ACTUATOR
            )
            yield from self._yield_series_points(
                time_index, site_id, asset_id, "relay_3", relay_3,
                "bool", DataType.BOOLEAN, PointType.ACTUATOR
            )
            yield from self._yield_series_points(
                time_index, site_id, asset_id, "relay_4", relay_4,
                "bool", DataType.BOOLEAN, PointType.ACTUATOR
            )
            yield from self._yield_series_points(
                time_index, site_id, asset_id, "power", power,
                "W", DataType.FLOAT, PointType.SENSOR
            )
            yield from self._yield_series_points(
                time_index, site_id, asset_id, "energy", energy,
                "kWh", DataType.FLOAT, PointType.SENSOR
            )

    def _yield_series_points(
        self,
        time_index: pd.DatetimeIndex,
        site_id: str,
        asset_id: str,
        variable: str,
        series: pd.Series,
        unit: str,
        data_type: DataType,
        point_type: PointType
    ) -> Iterator[DataPoint]:
        """Yield DataPoints from a time series."""
        pvn = build_pvn(asset_id, variable)

        for ts, val in series.items():
            yield DataPoint(
                timestamp=ts.to_pydatetime(),
                domain_id=self.domain_id,
                site_id=site_id,
                asset_id=asset_id,
                variable=variable,
                value=val,
                unit=unit,
                data_type=data_type,
                point_type=point_type,
                quality=Quality.OK,
                origin="synthetic",
                pvn=pvn,
            )

    def _yield_enum_points(
        self,
        time_index: pd.DatetimeIndex,
        site_id: str,
        asset_id: str,
        variable: str,
        series: pd.Series,
        enum_map: dict[str, int]
    ) -> Iterator[DataPoint]:
        """Yield DataPoints from an enum series."""
        pvn = build_pvn(asset_id, variable)
        mapped = series.map(enum_map)

        for ts, val in mapped.items():
            yield DataPoint(
                timestamp=ts.to_pydatetime(),
                domain_id=self.domain_id,
                site_id=site_id,
                asset_id=asset_id,
                variable=variable,
                value=val,
                unit="enum",
                data_type=DataType.ENUM,
                point_type=PointType.ACTUATOR,
                quality=Quality.OK,
                origin="synthetic",
                pvn=pvn,
            )

    def get_required_config_keys(self) -> list[str]:
        """Required configuration keys for BMS Classrooms."""
        return ["n_aulas"]

    def validate_config(
        self,
        project_cfg: dict[str, Any],
        domain_cfg: dict[str, Any]
    ) -> list[str]:
        """Validate BMS configuration."""
        errors = super().validate_config(project_cfg, domain_cfg)

        n_aulas = domain_cfg.get("n_aulas")
        if n_aulas is None:
            errors.append("Missing required config key: n_aulas")
        elif not isinstance(n_aulas, int) or n_aulas < 1:
            errors.append("n_aulas must be a positive integer")

        return errors
