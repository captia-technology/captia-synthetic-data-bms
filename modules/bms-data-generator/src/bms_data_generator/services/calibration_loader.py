"""Carga config de calibración (faults.yaml + physics overrides)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from bms_calibration.physics_overrides import get_overrides


def load_faults_config(faults_yaml: Path) -> dict[str, dict[str, Any]]:
    """Carga ``faults.yaml`` con probabilidades por tipo de fallo."""
    if not faults_yaml.exists():
        return {}
    with faults_yaml.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Invalid faults.yaml structure: {faults_yaml}")
    return data


def load_physics_overrides() -> dict[str, Any]:
    """Devuelve diccionario de overrides activos (puede estar vacío)."""
    return get_overrides()
