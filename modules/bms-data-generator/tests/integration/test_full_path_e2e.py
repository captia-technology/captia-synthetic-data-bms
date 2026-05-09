"""Integration test E2E: real ScenarioRunner + AliasSink + canonical schema.

Verifica que el path completo del generador (sin docker) produce datos
consistentes con producción simarro-prod:

  1. Variables emitidas == catálogo `production_name` esperado.
  2. Schema canonical compliance (asset_id uppercase, variable lowercase, 5 tags).
  3. AliasSink renombra correctamente (vendor → producción).
  4. Determinismo: 2 runs con mismo seed → mismo hash sha256.

Marker: ``integration`` — invoca el vendor sintético real (no fakes).
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
SCENARIOS_DIR = REPO_ROOT / "scripts"
OUTPUT_DIR = REPO_ROOT / "output"


# Variables que el vendor REALMENTE genera (post-AliasSink, alineadas con producción).
EXPECTED_PRODUCTION_VARIABLES = {
    # Environmental
    "temperature_01",
    "relative-humidity",
    "co2",
    "iaq-index",
    "avg-sound-level",
    "luminosity",
    # Occupancy
    "people-count",
    "occupancy",
    # External
    "temperature-outdoor",
    "daylight-lux",
    # HVAC actuators
    "temperature_01_sp",
    "ac_control",
    "ac_state",
    "valve_control",
    # Control relays
    "scene_mode",
    "light_01_state",
    "light_02_state",
    "fan_speed_01_state",
    "fan_speed_02_state",
    # Energy
    "power_01",
    "energy_01",
}


def _write_mini_scenario(tmp_path: Path, output_csv: Path, n_aulas: int = 2) -> Path:
    """Write a tiny scenario YAML for fast E2E validation.

    The scenario YAML filename is derived from output_csv stem, so distinct
    output paths yield distinct scenario files (avoids overwrites between
    paired runs in same tmp_path).
    """
    scenario = {
        "project": {
            "namespace": "captia",
            "site_id": "ies_simarro",
            "modo": "synthetic",
            "schema_version": "v0.1",
        },
        "simulation": {
            "timezone": "Europe/Madrid",
            "seed": 42,
            "start": "2026-01-15T00:00:00",
            "end": "2026-01-15T01:00:00",
            "freq": "5min",
            "n_aulas": n_aulas,
        },
        "domain": {"id": "bms_classrooms"},
        "phases": {"backfill": {"enabled": True}, "live": {"enabled": False}},
        "anomalies": {"p_missing": 0.0, "p_outlier": 0.0},
        "sinks": [{"type": "file", "config": {"path": str(output_csv), "format": "csv_long"}}],
        "output": {"format": "long", "include_quality": True, "include_mqtt": False},
    }
    path = tmp_path / f"scenario_{output_csv.stem}.yaml"
    path.write_text(yaml.safe_dump(scenario), encoding="utf-8")
    return path


def _run_scenario(scenario_path: Path, alias_enabled: bool = True) -> int:
    """Build and run scenario; return total points emitted."""
    os.environ["BMS_PRODUCTION_ALIAS_ENABLED"] = "true" if alias_enabled else "false"
    # Force re-read of cached settings.
    from bms_data_generator.config import reset_settings_cache
    reset_settings_cache()

    from bms_data_generator.services.runner_service import _build_runner

    result = _build_runner(scenario_path)
    runner, _sink = result[0], result[1]
    results = runner.run()
    return sum(getattr(r, "points_emitted", 0) for r in results)


def _read_csv_rows(csv_path: Path) -> list[dict]:
    """Read csv_long output as list of dicts."""
    import csv
    with csv_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


# ────────────────────── Test cases ──────────────────────


@pytest.mark.integration
@pytest.mark.slow
def test_e2e_alias_sink_emits_production_names(tmp_path: Path) -> None:
    """Con AliasSink habilitado, las variables emitidas coinciden con producción."""
    output_csv = tmp_path / "alias_e2e.csv"
    scenario = _write_mini_scenario(tmp_path, output_csv)

    total = _run_scenario(scenario, alias_enabled=True)
    assert total > 0, "no points emitted"
    assert output_csv.exists(), f"output not created at {output_csv}"

    rows = _read_csv_rows(output_csv)
    emitted_vars = {row["variable"] for row in rows}

    # Cada variable producción esperada debe aparecer.
    missing = EXPECTED_PRODUCTION_VARIABLES - emitted_vars
    assert not missing, f"variables esperadas faltantes: {missing}"

    # No debe haber variables vendor crudas (que tienen production_name override).
    vendor_only_names = {
        "temperature", "humidity", "noise", "illuminance", "iaq_index",
        "outdoor_temp", "daylight_lux", "thermostat_setpoint",
        "hvac_mode", "hvac_enable", "heating_valve_pos",
        "relay_1", "relay_2", "relay_3", "relay_4",
        "power", "energy", "presence_pir",
    }
    leaked_vendor = emitted_vars & vendor_only_names
    assert not leaked_vendor, f"nombres vendor leak en output: {leaked_vendor}"


@pytest.mark.integration
@pytest.mark.slow
def test_e2e_schema_canonical_compliance(tmp_path: Path) -> None:
    """Cada DataPoint cumple schema canónico CAPTIA: 5 tags + value, casing, no nulls."""
    output_csv = tmp_path / "schema_e2e.csv"
    scenario = _write_mini_scenario(tmp_path, output_csv)

    _run_scenario(scenario, alias_enabled=True)
    rows = _read_csv_rows(output_csv)
    assert rows, "no rows emitted"

    for row in rows[:200]:  # sample (rest is similar)
        # 5 tags presentes
        assert row["domain_id"] == "bms_classrooms"
        assert row["site_id"] == "ies_simarro"
        assert row["asset_id"], "asset_id empty"
        assert row["variable"], "variable empty"
        # casing
        assert row["asset_id"] == row["asset_id"].upper(), \
            f"asset_id not uppercase: {row['asset_id']}"
        assert row["variable"] == row["variable"].lower(), \
            f"variable not lowercase: {row['variable']}"
        # value field
        assert row["value"], f"value empty for {row['asset_id']}.{row['variable']}"
        # parseable as float
        try:
            float(row["value"])
        except ValueError:
            pytest.fail(f"value not parseable as float: {row['value']!r} for {row['variable']}")
        # timestamp ISO format
        assert "T" in row["timestamp"], f"timestamp not ISO: {row['timestamp']}"


@pytest.mark.integration
@pytest.mark.slow
def test_e2e_disable_alias_emits_vendor_names(tmp_path: Path) -> None:
    """Con AliasSink deshabilitado, las variables emitidas son los nombres vendor crudos."""
    output_csv = tmp_path / "no_alias_e2e.csv"
    scenario = _write_mini_scenario(tmp_path, output_csv)

    _run_scenario(scenario, alias_enabled=False)
    rows = _read_csv_rows(output_csv)
    emitted_vars = {row["variable"] for row in rows}

    # Vendor names presentes
    expected_vendor = {"temperature", "humidity", "power", "thermostat_setpoint", "hvac_mode"}
    missing = expected_vendor - emitted_vars
    assert not missing, f"vendor names esperados faltantes con alias OFF: {missing}"

    # Production names NO deben aparecer (los específicos)
    production_only = {"temperature_01", "relative-humidity", "power_01"}
    leaked_prod = emitted_vars & production_only
    assert not leaked_prod, f"production names leak con alias OFF: {leaked_prod}"


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.snapshot
def test_e2e_determinism_same_seed_same_hash(tmp_path: Path) -> None:
    """Dos runs con el mismo seed producen el mismo hash sha256 del output."""
    csv_a = tmp_path / "det_a.csv"
    csv_b = tmp_path / "det_b.csv"

    scen_a = _write_mini_scenario(tmp_path, csv_a)
    scen_b = _write_mini_scenario(tmp_path, csv_b)

    _run_scenario(scen_a, alias_enabled=True)
    _run_scenario(scen_b, alias_enabled=True)

    h_a = hashlib.sha256(csv_a.read_bytes()).hexdigest()
    h_b = hashlib.sha256(csv_b.read_bytes()).hexdigest()
    assert h_a == h_b, f"output hash mismatch: {h_a[:16]}... != {h_b[:16]}..."


@pytest.mark.integration
@pytest.mark.slow
def test_e2e_alias_count_consistency(tmp_path: Path) -> None:
    """AliasSink renamed_count + passthrough_count == total emitted."""
    output_csv = tmp_path / "count_e2e.csv"
    scenario = _write_mini_scenario(tmp_path, output_csv)

    os.environ["BMS_PRODUCTION_ALIAS_ENABLED"] = "true"
    from bms_data_generator.config import reset_settings_cache
    reset_settings_cache()
    from bms_data_generator.services.runner_service import _build_runner

    result = _build_runner(scenario)
    runner, sink = result[0], result[1]
    assert hasattr(sink, "renamed_count"), "sink should be AliasSinkAdapter"

    results = runner.run()
    total = sum(getattr(r, "points_emitted", 0) for r in results)
    assert total > 0
    # All emitted points went through rename or passthrough.
    assert sink.renamed_count + sink.passthrough_count == total, (
        f"counts mismatch: renamed={sink.renamed_count} + "
        f"passthrough={sink.passthrough_count} != total={total}"
    )
    # At least some rename happened (production override has 19 active aliases).
    assert sink.renamed_count > 0, "no renames despite alias enabled"
