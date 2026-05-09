"""Auditoría estática de dashboards Grafana ↔ catálogo de variables.

Verifica que cada referencia ``r.variable == "X"`` en queries Flux de
los dashboards usa nombres del catálogo `production_name` (lo que AliasSink
emite a InfluxDB).

Cierra gap detectado en auditoría: dashboards usaban `solar_irradiance`,
`temperature_outdoor`, `relative_humidity_01`, `avg_sound_level`, `people_count`
(snake_case) cuando AliasSink emite `daylight-lux`, `temperature-outdoor`,
`relative-humidity`, `avg-sound-level`, `people-count` (kebab-case).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DASHBOARDS_DIR = REPO_ROOT / "infra" / "grafana" / "dashboards"
VARIABLES_YAML = REPO_ROOT / "config" / "domains" / "bms_classrooms" / "variables.yaml"

# Matches both raw `r.variable == "X"` and JSON-escaped `r.variable == \"X\"`.
VAR_FILTER_PATTERN = re.compile(r'r\.variable\s*==\s*\\?"([a-zA-Z0-9_-]+)\\?"')


def _emitted_variable_names() -> set[str]:
    """Lista de nombres que el generador emite (production_name si existe, sino name)."""
    with VARIABLES_YAML.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    names = set()
    for var in data["asset_types"]["classroom"]["variables"]:
        names.add(var.get("production_name") or var["name"])
    # Variables internas que no se emiten (alimentan otras): light_state.
    # Variables sintéticas adicionales que dashboards podrían referenciar
    # como proxy: ninguna por ahora.
    return names


def _all_dashboards() -> list[Path]:
    return sorted(DASHBOARDS_DIR.glob("*.json"))


def _extract_variable_refs(dashboard_path: Path) -> set[str]:
    """Extrae todos los nombres de variable referenciados en queries Flux."""
    text = dashboard_path.read_text(encoding="utf-8")
    return set(VAR_FILTER_PATTERN.findall(text))


# ──────────────────── Tests ────────────────────


@pytest.mark.integration
def test_at_least_4_dashboards_provisioned() -> None:
    """Debe haber al menos 4 dashboards: overview + 3 use cases."""
    dashboards = _all_dashboards()
    assert len(dashboards) >= 4, f"esperado ≥4 dashboards, got {len(dashboards)}"


@pytest.mark.integration
@pytest.mark.parametrize("dashboard", _all_dashboards(), ids=lambda p: p.name)
def test_dashboard_is_valid_json(dashboard: Path) -> None:
    """Cada dashboard parsea como JSON válido."""
    json.loads(dashboard.read_text(encoding="utf-8"))


@pytest.mark.integration
@pytest.mark.parametrize("dashboard", _all_dashboards(), ids=lambda p: p.name)
def test_dashboard_has_uid(dashboard: Path) -> None:
    """Cada dashboard tiene UID (necesario para deep-links y provisioning)."""
    data = json.loads(dashboard.read_text(encoding="utf-8"))
    uid = data.get("uid")
    assert uid, f"{dashboard.name} sin uid"
    assert isinstance(uid, str) and len(uid) > 0


@pytest.mark.integration
@pytest.mark.parametrize("dashboard", _all_dashboards(), ids=lambda p: p.name)
def test_dashboard_variables_match_catalog(dashboard: Path) -> None:
    """Cada r.variable == "X" en queries Flux debe ser una variable emitida.

    Si falla: el panel queda vacío en producción porque consulta una variable
    que el generador NO emite (regresión clásica al cambiar nombres vendor↔prod).
    """
    catalog = _emitted_variable_names()
    refs = _extract_variable_refs(dashboard)

    invalid = refs - catalog
    assert not invalid, (
        f"{dashboard.name}: variables referenciadas que NO están en catálogo: {invalid}\n"
        f"Catálogo (production_names emitidos): {sorted(catalog)}"
    )


@pytest.mark.integration
def test_dashboard_caseB_uses_production_naming() -> None:
    """Caso B (consumption) debe usar nombres producción (kebab-case mix)."""
    dashboard = DASHBOARDS_DIR / "bms_consumption_caseB.json"
    refs = _extract_variable_refs(dashboard)
    # Debe estar power_01 (sufijo _NN canónico).
    assert "power_01" in refs, f"caseB no usa power_01: {refs}"
    # NO debe estar el nombre vendor crudo "power"
    assert "power" not in refs, "caseB referencia vendor name 'power' en lugar de 'power_01'"


@pytest.mark.integration
def test_dashboard_caseD_uses_production_naming() -> None:
    """Caso D (IAQ) debe usar nombres producción (kebab-case)."""
    dashboard = DASHBOARDS_DIR / "bms_iaq_caseD.json"
    refs = _extract_variable_refs(dashboard)
    # Variables IAQ con kebab-case obligatorio
    assert "relative-humidity" in refs, "caseD no usa relative-humidity (kebab)"
    assert "people-count" in refs, "caseD no usa people-count (kebab)"
    assert "avg-sound-level" in refs, "caseD no usa avg-sound-level (kebab)"
    # Y NO los snake_case originales
    assert "relative_humidity_01" not in refs
    assert "people_count" not in refs
    assert "avg_sound_level" not in refs


@pytest.mark.integration
@pytest.mark.parametrize("dashboard", _all_dashboards(), ids=lambda p: p.name)
def test_dashboard_uses_canonical_measurement(dashboard: Path) -> None:
    """Las queries Flux deben usar measurement ``captia_point`` (no legacy)."""
    text = dashboard.read_text(encoding="utf-8")
    # Si tiene queries con _measurement, debe usar captia_point (no captia_metric o legacy)
    if "_measurement" in text:
        # No debe haber referencias a measurements legacy
        assert "captia_metric" not in text, f"{dashboard.name} referencia measurement legacy 'captia_metric'"
