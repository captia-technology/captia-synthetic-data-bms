"""Auditoría estática de las 6 Flux tasks de downsampling.

Verifica:
  1. Cada task referencia el measurement correcto en cada bucket
     (captia_point en telemetry, captia_point_state en state_events vía workaround
     L-PV-19, captia_point_meta en captia_metadata).
  2. Cada task de tier-1 filtra por metric_kind correcto (allowlist desde catalog).
  3. Cada metric_kind del catálogo está cubierto por al menos una Flux task.
  4. Las tasks tier-2/3 (cascada) preservan el tag stat.

Cierra parte de L-PV-21 (rollups consistentes con catálogo).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
TASKS_DIR = REPO_ROOT / "infra" / "influxdb" / "tasks"
VARIABLES_YAML = REPO_ROOT / "config" / "domains" / "bms_classrooms" / "variables.yaml"


def _read_task(name: str) -> str:
    path = TASKS_DIR / f"{name}.flux"
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _all_metric_kinds_in_catalog() -> set[str]:
    with VARIABLES_YAML.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return {v["metric_kind"] for v in data["asset_types"]["classroom"]["variables"]}


# ──────────────────── Tests ────────────────────


@pytest.mark.integration
def test_six_tier_tasks_exist() -> None:
    """Las 6 Flux tasks existen como ficheros."""
    expected = [
        "downsample_analog_1m",
        "downsample_presence_1m",
        "downsample_state_1m",
        "downsample_counter_1m",
        "downsample_15m",
        "downsample_1h",
    ]
    for name in expected:
        path = TASKS_DIR / f"{name}.flux"
        assert path.exists(), f"missing Flux task: {name}.flux"


@pytest.mark.integration
def test_tier1_tasks_query_captia_point_meta() -> None:
    """Las tier-1 tasks consultan captia_metadata bucket con measurement captia_point_meta."""
    tier1 = [
        "downsample_analog_1m",
        "downsample_presence_1m",
        "downsample_state_1m",
        "downsample_counter_1m",
    ]
    for name in tier1:
        flux = _read_task(name)
        assert flux, f"task file empty: {name}"
        assert 'from(bucket: "captia_metadata")' in flux, (
            f"{name} no consulta captia_metadata bucket"
        )
        assert 'r._measurement == "captia_point_meta"' in flux, (
            f"{name} no filtra _measurement == captia_point_meta"
        )
        assert 'r._field == "metric_kind"' in flux, f"{name} no filtra _field == metric_kind"


@pytest.mark.integration
def test_analog_task_filters_by_analog_gauge() -> None:
    flux = _read_task("downsample_analog_1m")
    assert 'r._value == "analog_gauge"' in flux


@pytest.mark.integration
def test_presence_task_filters_by_bool_presence() -> None:
    flux = _read_task("downsample_presence_1m")
    assert 'r._value == "bool_presence"' in flux


@pytest.mark.integration
def test_state_task_filters_bool_state_and_setpoint_step() -> None:
    flux = _read_task("downsample_state_1m")
    assert 'r._value == "bool_state"' in flux
    assert 'r._value == "setpoint_step"' in flux


@pytest.mark.integration
def test_counter_task_filters_by_counter() -> None:
    flux = _read_task("downsample_counter_1m")
    assert 'r._value == "counter"' in flux


@pytest.mark.integration
def test_state_task_uses_state_events_bucket() -> None:
    """downsample_state_1m lee state_events bucket (L-PV-19 workaround: captia_point_state)."""
    flux = _read_task("downsample_state_1m")
    assert 'from(bucket: "state_events")' in flux
    # L-PV-19 workaround: nuestro Telegraf escribe captia_point_state (vendor name_override)
    assert 'r._measurement == "captia_point_state"' in flux, (
        "downsample_state_1m debería filtrar captia_point_state (workaround L-PV-19)"
    )


@pytest.mark.integration
def test_continuous_tasks_use_telemetry_bucket() -> None:
    """analog/presence/counter tier-1 leen del bucket telemetry."""
    for name in ["downsample_analog_1m", "downsample_presence_1m", "downsample_counter_1m"]:
        flux = _read_task(name)
        assert 'from(bucket: "telemetry")' in flux, f"{name} debería leer telemetry"
        assert 'r._measurement == "captia_point"' in flux, (
            f"{name} debería filtrar captia_point en telemetry"
        )


@pytest.mark.integration
def test_all_tier1_tasks_write_to_telemetry_1m() -> None:
    """Las 4 tasks tier-1 escriben a telemetry_1m bucket."""
    for name in [
        "downsample_analog_1m",
        "downsample_presence_1m",
        "downsample_state_1m",
        "downsample_counter_1m",
    ]:
        flux = _read_task(name)
        assert 'to(bucket: "telemetry_1m"' in flux, f"{name} debería escribir a telemetry_1m"


@pytest.mark.integration
def test_cascade_tasks_preserve_stat_tag() -> None:
    """Las tasks 15m y 1h preservan el tag stat de la cascada (r.stat == ...)."""
    for name in ["downsample_15m", "downsample_1h"]:
        flux = _read_task(name)
        # Cascade tasks use `r.stat == "mean"` etc. as filters per stat type.
        has_stat_handling = "r.stat ==" in flux or 'set(key: "stat"' in flux
        assert has_stat_handling, f"{name} debería filtrar/setear el tag stat en cascada"


@pytest.mark.integration
def test_cascade_tasks_handle_all_stats() -> None:
    """Las tasks cascada manejan los 6 stats: mean, min, max, sum, last, count_rise."""
    expected_stats = {"mean", "min", "max", "sum", "last", "count_rise"}
    for name in ["downsample_15m", "downsample_1h"]:
        flux = _read_task(name)
        # duty cascades as mean, so we accept duty too.
        for stat in expected_stats:
            assert f'"{stat}"' in flux, f"{name} no maneja stat={stat}"


@pytest.mark.integration
def test_all_metric_kinds_in_catalog_have_a_flux_task() -> None:
    """Cada metric_kind del catálogo está cubierto por al menos una Flux task."""
    catalog_kinds = _all_metric_kinds_in_catalog()
    catalog_kinds.discard("skip")

    coverage = {
        "analog_gauge": "downsample_analog_1m",
        "bool_presence": "downsample_presence_1m",
        "bool_state": "downsample_state_1m",
        "setpoint_step": "downsample_state_1m",
        "counter": "downsample_counter_1m",
    }
    uncovered = catalog_kinds - set(coverage)
    assert not uncovered, f"metric_kinds del catálogo sin Flux task: {uncovered}"

    for kind, task_name in coverage.items():
        if kind not in catalog_kinds:
            continue
        flux = _read_task(task_name)
        assert f'"{kind}"' in flux, f"task {task_name} no referencia {kind}"
