"""Context builder for Industrial Refrigeration domain.

Creates simulation context with weather driver and plant configuration.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

from .physics.meteo import MeteoDriver, generate_synthetic_weather, load_weather_from_file


@dataclass
class RefrigerationContext:
    """Simulation context for Industrial Refrigeration domain.

    Contains shared state used across all plant simulations.

    Attributes:
        time_index: Time points for simulation
        meteo: Weather data driver
        physics_cfg: Physics configuration dict
        chamber_setpoints: Per-chamber temperature setpoints
        rng: NumPy random generator
    """
    time_index: pd.DatetimeIndex
    meteo: MeteoDriver
    physics_cfg: dict[str, Any]
    chamber_setpoints: dict[str, float]
    rng: np.random.Generator


def build_refrigeration_context(
    time_index: pd.DatetimeIndex,
    project_cfg: dict[str, Any],
    domain_cfg: dict[str, Any],
    rng: np.random.Generator
) -> RefrigerationContext:
    """Build simulation context for Industrial Refrigeration domain.

    Args:
        time_index: Time points for simulation
        project_cfg: Project-level configuration
        domain_cfg: Domain-specific configuration (from industrial_refrigeration.yaml)
        rng: NumPy random generator

    Returns:
        RefrigerationContext with all shared state
    """
    # Get physics configuration
    physics_cfg = domain_cfg.get("physics", {})

    # Build weather driver
    meteo_source = domain_cfg.get("meteo_source", "synthetic")
    meteo_cfg = physics_cfg.get("global", {})

    if meteo_source == "synthetic":
        meteo = generate_synthetic_weather(time_index, meteo_cfg, rng)
    elif Path(meteo_source).exists():
        meteo = load_weather_from_file(time_index, Path(meteo_source), meteo_cfg)
    else:
        # Default to synthetic
        meteo = generate_synthetic_weather(time_index, meteo_cfg, rng)

    # Build chamber setpoints
    # Default setpoints per chamber type
    chamber_setpoints = {}
    inv_cfg = domain_cfg.get("inventory", {})
    assets_cfg = inv_cfg.get("assets", [])

    for asset_def in assets_cfg:
        if asset_def.get("asset_type") == "cold_room":
            if "asset_ids" in asset_def:
                for cid in asset_def["asset_ids"]:
                    # Vary setpoints: frozen (-20 to -25) vs fresh (-2 to +5)
                    idx = int(cid.replace("CAMARA", "")) if "CAMARA" in cid else 0
                    if idx <= 6:
                        # Frozen chambers
                        sp = -20.0 + rng.normal(0, 2)
                    else:
                        # Fresh/chilled chambers
                        sp = 2.0 + rng.normal(0, 1)
                    chamber_setpoints[cid] = float(np.clip(sp, -30, 10))

    # Ensure we have setpoints for all 10 default chambers
    for i in range(1, 11):
        cid = f"CAMARA{i}"
        if cid not in chamber_setpoints:
            if i <= 6:
                chamber_setpoints[cid] = -20.0 + rng.normal(0, 2)
            else:
                chamber_setpoints[cid] = 2.0 + rng.normal(0, 1)

    return RefrigerationContext(
        time_index=time_index,
        meteo=meteo,
        physics_cfg=physics_cfg,
        chamber_setpoints=chamber_setpoints,
        rng=rng
    )
