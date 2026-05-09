"""Calibration module for Industrial Refrigeration.

Provides tools to learn statistics from real data samples
to improve synthetic data realism.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Optional
import logging

import numpy as np
import pandas as pd

LOG = logging.getLogger("synthetic_generator.domains.industrial_refrigeration.calibration")


def calibrate_from_sample(
    sample_path: Path,
    output_path: Optional[Path] = None
) -> dict[str, Any]:
    """Calibrate domain parameters from sample data.

    Analyzes real data to extract statistics for:
    - Temperature distributions per chamber
    - Pressure ranges
    - Power consumption patterns
    - Control behavior (on/off cycles, defrost patterns)

    Args:
        sample_path: Path to sample CSV file
        output_path: Optional path to write calibrated YAML config

    Returns:
        Dictionary of calibrated parameters
    """
    LOG.info("Loading sample data from %s", sample_path)

    df = pd.read_csv(sample_path)

    if "timestamp" in df.columns or "fecha" in df.columns:
        ts_col = "timestamp" if "timestamp" in df.columns else "fecha"
        df[ts_col] = pd.to_datetime(df[ts_col])
        df.set_index(ts_col, inplace=True)

    calibration = {
        "calibrated_from": str(sample_path),
        "sample_rows": len(df),
    }

    # Detect column format
    # Check if wide format (columns like "camara1__temperatura")
    if any("__" in col for col in df.columns):
        calibration.update(_calibrate_wide_format(df))
    else:
        calibration.update(_calibrate_long_format(df))

    if output_path:
        import yaml
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(calibration, f, default_flow_style=False)
        LOG.info("Wrote calibrated config to %s", output_path)

    return calibration


def _calibrate_wide_format(df: pd.DataFrame) -> dict[str, Any]:
    """Calibrate from wide format data (columns like asset__variable)."""
    result = {
        "chambers": {},
        "compressors": {},
        "condenser": {},
        "energy": {},
    }

    # Extract chamber statistics
    chamber_cols = [c for c in df.columns if c.lower().startswith("camara")]
    for col in chamber_cols:
        parts = col.split("__")
        if len(parts) == 2:
            asset, var = parts[0], parts[1]
            asset = asset.upper()

            if asset not in result["chambers"]:
                result["chambers"][asset] = {}

            values = pd.to_numeric(df[col], errors="coerce").dropna()
            if len(values) > 0:
                result["chambers"][asset][var] = {
                    "mean": float(values.mean()),
                    "std": float(values.std()),
                    "min": float(values.min()),
                    "max": float(values.max()),
                    "p5": float(values.quantile(0.05)),
                    "p95": float(values.quantile(0.95)),
                }

    # Extract compressor statistics
    comp_cols = [c for c in df.columns if "compresor" in c.lower() or "compressor" in c.lower()]
    for col in comp_cols:
        values = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(values) > 0:
            result["compressors"][col] = {
                "mean": float(values.mean()),
                "on_fraction": float((values > 0).mean()),
            }

    # Extract energy statistics
    energy_cols = [c for c in df.columns if "power" in c.lower() or "energy" in c.lower()]
    for col in energy_cols:
        values = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(values) > 0:
            result["energy"][col] = {
                "mean": float(values.mean()),
                "std": float(values.std()),
                "max": float(values.max()),
            }

    return result


def _calibrate_long_format(df: pd.DataFrame) -> dict[str, Any]:
    """Calibrate from long format data (rows with asset_id, variable, value)."""
    result = {
        "chambers": {},
        "compressors": {},
        "condenser": {},
        "energy": {},
    }

    # Identify asset and variable columns
    asset_col = None
    var_col = None
    val_col = None

    for col in ["asset_id", "aula_id", "punto_id"]:
        if col in df.columns:
            asset_col = col
            break

    for col in ["variable", "variable_name"]:
        if col in df.columns:
            var_col = col
            break

    for col in ["value", "valor"]:
        if col in df.columns:
            val_col = col
            break

    if not all([asset_col, var_col, val_col]):
        LOG.warning("Could not identify required columns for long format calibration")
        return result

    # Group and calculate statistics
    for asset_id in df[asset_col].unique():
        asset_df = df[df[asset_col] == asset_id]
        asset_upper = str(asset_id).upper()

        if "CAMARA" in asset_upper:
            if asset_upper not in result["chambers"]:
                result["chambers"][asset_upper] = {}

            for var in asset_df[var_col].unique():
                var_df = asset_df[asset_df[var_col] == var]
                values = pd.to_numeric(var_df[val_col], errors="coerce").dropna()

                if len(values) > 0:
                    result["chambers"][asset_upper][var] = {
                        "mean": float(values.mean()),
                        "std": float(values.std()),
                    }

        elif "ENERGIA" in asset_upper or "ENERGY" in asset_upper:
            for var in asset_df[var_col].unique():
                var_df = asset_df[asset_df[var_col] == var]
                values = pd.to_numeric(var_df[val_col], errors="coerce").dropna()

                if len(values) > 0:
                    result["energy"][var] = {
                        "mean": float(values.mean()),
                        "std": float(values.std()),
                        "max": float(values.max()),
                    }

    return result


def suggest_chamber_setpoints(calibration: dict[str, Any]) -> dict[str, float]:
    """Suggest chamber setpoints based on calibration data."""
    setpoints = {}

    for chamber_id, stats in calibration.get("chambers", {}).items():
        if "temperature" in stats or "temperatura" in stats:
            temp_stats = stats.get("temperature", stats.get("temperatura", {}))
            # Use mean as setpoint estimate
            setpoints[chamber_id] = temp_stats.get("mean", -20.0)

    return setpoints
