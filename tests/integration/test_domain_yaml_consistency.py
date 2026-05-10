"""Auditoría estática de consistencia ``domain.yaml`` ↔ physics keys (T-PV-50, L-PV-03).

Verifica que cada clave en la sección ``physics`` del override
``config/domains/bms_classrooms/domain.yaml`` es leída por al menos una función
de ``vendor/.../physics/*.py``. Sin esta consistencia, el override es
silenciosamente inerte.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DOMAIN_YAML = REPO_ROOT / "config" / "domains" / "bms_classrooms" / "domain.yaml"
PHYSICS_DIR = (
    REPO_ROOT
    / "vendor"
    / "synthetic-generator"
    / "src"
    / "synthetic_generator"
    / "domains"
    / "bms_classrooms"
    / "physics"
)


def _yaml_physics_keys() -> set[str]:
    """Set de claves leaf de ``physics: <subsection>: <key>: <val>``."""
    with DOMAIN_YAML.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    keys: set[str] = set()
    for _section, subdict in data.get("physics", {}).items():
        if isinstance(subdict, dict):
            keys.update(subdict.keys())
    return keys


def _physics_code_keys() -> set[str]:
    """Set de claves leídas via ``cfg.get("KEY")`` en physics/*.py."""
    pattern = re.compile(r'\.get\(\s*"([a-z_][a-z_0-9]*)"')
    keys: set[str] = set()
    for py in PHYSICS_DIR.glob("*.py"):
        for match in pattern.finditer(py.read_text(encoding="utf-8")):
            keys.add(match.group(1))
    return keys


@pytest.mark.integration
def test_all_yaml_physics_keys_are_read_by_code() -> None:
    """Cada clave en domain.yaml::physics debe ser leída por al menos una función physics.

    Si falla: el override en yaml es INERTE (no afecta el comportamiento del generador).
    Es exactamente el bug L-PV-03 detectado durante la auditoría.
    """
    yaml_keys = _yaml_physics_keys()
    code_keys = _physics_code_keys()
    inert = yaml_keys - code_keys
    assert not inert, (
        f"claves en domain.yaml::physics NO leídas por physics/*.py — override INERTE: {inert}\n"
        f"Migrar a las claves canónicas que el código realmente lee:\n"
        f"  Disponibles: {sorted(code_keys)}"
    )


@pytest.mark.integration
def test_yaml_physics_keys_coverage_is_high() -> None:
    """El override yaml debe cubrir al menos 50% de las claves físicas del código.

    Cobertura baja indica que la mayoría de los parámetros físicos siguen los
    defaults hardcoded del vendor — si se cambia el vendor, el comportamiento
    cambia silenciosamente.
    """
    yaml_keys = _yaml_physics_keys()
    code_keys = _physics_code_keys()
    coverage = len(yaml_keys & code_keys) / len(code_keys) if code_keys else 0
    assert coverage >= 0.5, (
        f"cobertura override yaml ↔ physics keys: {coverage:.1%} (≥50% esperado)\n"
        f"yaml: {sorted(yaml_keys)}\n"
        f"código: {sorted(code_keys)}"
    )


@pytest.mark.integration
def test_critical_physics_keys_are_overridable_via_yaml() -> None:
    """Las claves físicas más sensibles (térmica, CO2, HVAC) deben tener override yaml."""
    yaml_keys = _yaml_physics_keys()
    critical = {
        "tau_minutes",  # térmica RC
        "occupancy_heat_gain_c_per_person",  # ganancia personas
        "outdoor_ppm",  # CO2 baseline
        "gen_ppm_per_min_per_person",  # tasa generación CO2
        "vent_k_per_min",  # ventilación HVAC
        "leak_k_per_min",  # leak natural
        "setpoint_class",  # setpoint clase
        "setpoint_out_of_hours",  # setpoint OOH
        "mean_annual",  # T_outdoor anual
        "amplitude",  # T_outdoor amplitud
    }
    missing = critical - yaml_keys
    assert not missing, (
        f"claves físicas críticas SIN override yaml (vendor defaults sin control): {missing}"
    )
