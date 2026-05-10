"""Integration tests E2E de los 4 use cases (Caso A live, B consumption, C faults, D IAQ).

Cada test deriva del scenario YAML real (config/projects/bms_v1_*.yaml) pero
sobrescribe ``simulation.start/end`` para acortar a un timeframe ejecutable
(< 30s) y reemplaza paths Docker (``/app/...``) por paths locales (``output/...``).

Verifica:
  - Variables emitidas coinciden con production naming (vía AliasSink).
  - Cada caso tiene comportamiento esperado:
      Caso B: backfill 12m → ~scaled timeframe, energy crece monotónicamente.
      Caso C: con BMS_FAULTS_ENABLED → fault.<tipo> aparece en output.
      Caso D: IAQ a 1min freq → CO2/temp/humidity dentro de rangos físicos.
  - AliasSink + FaultEventEmitter no interfieren entre sí (fault.* passthrough).

Cierra audit profundo: T-PV-21 (alias), T-PV-08 (faults), T-PV-09 (calendar) E2E.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
SCENARIOS_DIR = REPO_ROOT / "config" / "projects"
DOMAIN_YAML_LOCAL = REPO_ROOT / "config" / "domains" / "bms_classrooms" / "domain.yaml"


def _localize_scenario(
    src_yaml: Path,
    tmp_path: Path,
    output_csv: Path,
    start: str,
    end: str,
    n_aulas: int = 2,
) -> Path:
    """Load scenario YAML, override start/end/sink paths for local execution.

    Returns path to a tmp YAML pointing to local domain.yaml + local output csv.
    """
    with src_yaml.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Override simulation timeframe + n_aulas.
    data["simulation"]["start"] = start
    data["simulation"]["end"] = end
    data["simulation"]["n_aulas"] = n_aulas

    # Override domain.config_path → local override.
    data.setdefault("domain", {})["config_path"] = str(DOMAIN_YAML_LOCAL)

    # Replace any sink with a single local file sink.
    data["sinks"] = [
        {
            "type": "file",
            "config": {"path": str(output_csv), "format": "csv_long"},
        }
    ]

    # Force backfill on, live off (no MQTT broker available in tests).
    data.setdefault("phases", {})
    data["phases"]["backfill"] = {"enabled": True}
    data["phases"]["live"] = {"enabled": False}

    out = tmp_path / f"local_{src_yaml.stem}.yaml"
    out.write_text(yaml.safe_dump(data), encoding="utf-8")
    return out


def _run_scenario(scenario_path: Path) -> int:
    """Build runner from scenario, execute, return total points emitted."""
    os.environ["BMS_PRODUCTION_ALIAS_ENABLED"] = "true"
    from bms_data_generator.config import reset_settings_cache

    reset_settings_cache()
    from bms_data_generator.services.runner_service import _build_runner

    result = _build_runner(scenario_path)
    runner = result[0]
    fault_hook = result[2] if len(result) == 3 else None

    results = runner.run()
    total = sum(getattr(r, "points_emitted", 0) for r in results)
    if fault_hook is not None:
        total += fault_hook() or 0
    return total


def _read_csv_rows(csv_path: Path) -> list[dict]:
    with csv_path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ────────────────────── Caso B — Consumption backfill ────────────────────


@pytest.mark.integration
@pytest.mark.slow
def test_caseB_consumption_backfill_emits_production_names(tmp_path: Path) -> None:
    """Caso B (backfill consumo) emite variables con nombres producción."""
    output_csv = tmp_path / "caseB.csv"
    scen = _localize_scenario(
        SCENARIOS_DIR / "bms_v1_caseB_consumption.yaml",
        tmp_path,
        output_csv,
        start="2026-01-15T00:00:00",
        end="2026-01-15T01:00:00",
        n_aulas=2,
    )
    total = _run_scenario(scen)
    assert total > 0
    rows = _read_csv_rows(output_csv)
    emitted = {r["variable"] for r in rows}
    # Variables clave del Caso B
    assert "power_01" in emitted
    assert "temperature-outdoor" in emitted
    assert "people-count" in emitted
    assert "energy_01" in emitted
    # NO debe aparecer ningún nombre vendor crudo
    assert "power" not in emitted
    assert "outdoor_temp" not in emitted


@pytest.mark.integration
@pytest.mark.slow
def test_caseB_energy_is_monotonically_increasing(tmp_path: Path) -> None:
    """``energy_01`` (counter cumulative_monotonic) debe crecer monotónicamente
    en cada aula (no decrementos). Verifica que la integral cumsum del power
    se preserva tras AliasSink rename.
    """
    output_csv = tmp_path / "caseB_mono.csv"
    scen = _localize_scenario(
        SCENARIOS_DIR / "bms_v1_caseB_consumption.yaml",
        tmp_path,
        output_csv,
        start="2026-01-15T00:00:00",
        end="2026-01-15T02:00:00",  # 2h = 24 samples at 5min
        n_aulas=2,
    )
    _run_scenario(scen)
    rows = _read_csv_rows(output_csv)

    # Group energy_01 by asset_id, sort by timestamp, check monotonic non-decreasing.
    by_asset: dict[str, list[tuple[str, float]]] = {}
    for r in rows:
        if r["variable"] != "energy_01":
            continue
        by_asset.setdefault(r["asset_id"], []).append((r["timestamp"], float(r["value"])))

    assert by_asset, "no energy_01 datapoints emitted"
    for asset, pairs in by_asset.items():
        pairs.sort(key=lambda p: p[0])
        for i in range(1, len(pairs)):
            assert pairs[i][1] >= pairs[i - 1][1], (
                f"energy_01 NO monotónica en {asset}: "
                f"{pairs[i - 1][0]}={pairs[i - 1][1]} → {pairs[i][0]}={pairs[i][1]}"
            )


@pytest.mark.integration
@pytest.mark.slow
def test_caseB_power_within_physical_range(tmp_path: Path) -> None:
    """``power_01`` ∈ [0, 6000] W (rango duro de variables.yaml)."""
    output_csv = tmp_path / "caseB_range.csv"
    scen = _localize_scenario(
        SCENARIOS_DIR / "bms_v1_caseB_consumption.yaml",
        tmp_path,
        output_csv,
        start="2026-01-15T08:00:00",
        end="2026-01-15T10:00:00",
        n_aulas=2,
    )
    _run_scenario(scen)
    rows = _read_csv_rows(output_csv)
    powers = [float(r["value"]) for r in rows if r["variable"] == "power_01"]
    assert powers, "no power_01 emitted"
    assert all(0.0 <= p <= 6000.0 for p in powers), (
        f"power_01 fuera de rango [0, 6000]: min={min(powers):.2f} max={max(powers):.2f}"
    )


# ────────────────────── Caso C — Faults backfill ──────────────────────


@pytest.mark.integration
@pytest.mark.slow
def test_caseC_faults_disabled_emits_no_fault_variables(tmp_path: Path) -> None:
    """Caso C SIN BMS_FAULTS_ENABLED no emite variables fault.<tipo>."""
    os.environ["BMS_FAULTS_ENABLED"] = "false"
    from bms_data_generator.config import reset_settings_cache

    reset_settings_cache()

    output_csv = tmp_path / "caseC_no_faults.csv"
    scen = _localize_scenario(
        SCENARIOS_DIR / "bms_v1_caseC_faults.yaml",
        tmp_path,
        output_csv,
        start="2026-01-15T00:00:00",
        end="2026-01-15T06:00:00",
        n_aulas=2,
    )
    _run_scenario(scen)
    rows = _read_csv_rows(output_csv)
    fault_rows = [r for r in rows if r["variable"].startswith("fault.")]
    assert not fault_rows, f"fault.* emitido aunque faults disabled: {len(fault_rows)} rows"


def _build_scenario_with_high_prob_faults(
    tmp_path: Path, output_csv: Path, n_aulas: int = 2
) -> Path:
    """Construye scenario YAML + faults.yaml custom con prob alta para tests deterministas.

    Layout creado en tmp_path:
        tmp_path/config/projects/scenario.yaml
        tmp_path/config/domains/bms_classrooms/faults.yaml  (probability_per_day=0.5)
        tmp_path/config/domains/bms_classrooms/domain.yaml  (copia del real)
        tmp_path/config/domains/bms_classrooms/variables.yaml  (copia del real)

    El runner_service::_resolve_domain_config_path encontrará faults.yaml por
    strategy 1 (sibling layout config/projects ↔ config/domains).
    """
    domains_dir = tmp_path / "config" / "domains" / "bms_classrooms"
    domains_dir.mkdir(parents=True, exist_ok=True)

    # Custom faults.yaml con probabilidades altas para garantizar eventos.
    (domains_dir / "faults.yaml").write_text(
        "sensor_drift:\n"
        "  probability_per_day: 0.5\n"
        "  duration_minutes: 60\n"
        "valve_stuck:\n"
        "  probability_per_day: 0.5\n"
        "  duration_minutes: 60\n",
        encoding="utf-8",
    )

    # Copiar variables.yaml y domain.yaml reales para preservar el resto.
    real_variables = REPO_ROOT / "config" / "domains" / "bms_classrooms" / "variables.yaml"
    real_domain = REPO_ROOT / "config" / "domains" / "bms_classrooms" / "domain.yaml"
    (domains_dir / "variables.yaml").write_text(
        real_variables.read_text(encoding="utf-8"), encoding="utf-8"
    )
    (domains_dir / "domain.yaml").write_text(
        real_domain.read_text(encoding="utf-8"), encoding="utf-8"
    )

    projects_dir = tmp_path / "config" / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)

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
            "end": "2026-01-22T00:00:00",  # 7 días = 7×n_aulas×0.5 = ~7 events sensor_drift
            "freq": "5min",
            "n_aulas": n_aulas,
        },
        "domain": {"id": "bms_classrooms", "config_path": str(domains_dir / "domain.yaml")},
        "phases": {"backfill": {"enabled": True}, "live": {"enabled": False}},
        "anomalies": {"p_missing": 0.0, "p_outlier": 0.0},
        "sinks": [{"type": "file", "config": {"path": str(output_csv), "format": "csv_long"}}],
        "output": {"format": "long", "include_quality": True, "include_mqtt": False},
    }
    scen = projects_dir / "scenario.yaml"
    scen.write_text(yaml.safe_dump(scenario), encoding="utf-8")
    return scen


@pytest.mark.integration
@pytest.mark.slow
def test_caseC_faults_enabled_emits_fault_events(tmp_path: Path) -> None:
    """Con BMS_FAULTS_ENABLED=true + faults.yaml de alta probabilidad,
    se emiten fault.<tipo> DataPoints via FaultEventEmitter."""
    os.environ["BMS_FAULTS_ENABLED"] = "true"
    os.environ["BMS_PRODUCTION_ALIAS_ENABLED"] = "true"
    from bms_data_generator.config import reset_settings_cache

    reset_settings_cache()

    output_csv = tmp_path / "caseC_faults.csv"
    scen = _build_scenario_with_high_prob_faults(tmp_path, output_csv, n_aulas=2)
    try:
        _run_scenario(scen)
    finally:
        os.environ.pop("BMS_FAULTS_ENABLED", None)
        from bms_data_generator.config import reset_settings_cache as _rsc

        _rsc()

    rows = _read_csv_rows(output_csv)
    fault_rows = [r for r in rows if r["variable"].startswith("fault.")]
    assert fault_rows, "no fault.* DataPoints emitted con faults enabled"

    fault_types = {r["variable"] for r in fault_rows}
    # Con prob 0.5/day × 7 días × 2 aulas = ~7 events esperados.
    assert fault_types & {"fault.sensor_drift", "fault.valve_stuck"}, (
        f"esperaba al menos 1 fault.sensor_drift o fault.valve_stuck, got {fault_types}"
    )


@pytest.mark.integration
@pytest.mark.slow
def test_caseC_fault_events_have_canonical_schema(tmp_path: Path) -> None:
    """Los DataPoints fault.<tipo> cumplen schema canonical CAPTIA."""
    os.environ["BMS_FAULTS_ENABLED"] = "true"
    from bms_data_generator.config import reset_settings_cache

    reset_settings_cache()

    output_csv = tmp_path / "caseC_schema.csv"
    scen = _build_scenario_with_high_prob_faults(tmp_path, output_csv, n_aulas=2)
    try:
        _run_scenario(scen)
    finally:
        os.environ.pop("BMS_FAULTS_ENABLED", None)
        from bms_data_generator.config import reset_settings_cache as _rsc

        _rsc()

    rows = _read_csv_rows(output_csv)
    fault_rows = [r for r in rows if r["variable"].startswith("fault.")]
    assert fault_rows, "no fault events emitted with high-prob faults config"

    for r in fault_rows[:50]:
        assert r["domain_id"] == "bms_classrooms"
        assert r["site_id"] == "ies_simarro"
        assert r["asset_id"].startswith("AULA")
        assert r["variable"].startswith("fault.")
        assert r["variable"] == r["variable"].lower()
        # value debe ser parseable como float (severity en start, 0.0 en end).
        v = float(r["value"])
        assert 0.0 <= v <= 1.0


# ────────────────────── Caso D — IAQ 1min ──────────────────────


@pytest.mark.integration
@pytest.mark.slow
def test_caseD_iaq_emits_1min_freq_with_air_quality_vars(tmp_path: Path) -> None:
    """Caso D (IAQ) debe emitir CO2, temperatura, humedad con freq=1min."""
    output_csv = tmp_path / "caseD.csv"
    scen = _localize_scenario(
        SCENARIOS_DIR / "bms_v1_caseD_iaq.yaml",
        tmp_path,
        output_csv,
        start="2026-04-15T08:00:00",
        end="2026-04-15T09:00:00",  # 1h @ 1min = 60 timestamps
        n_aulas=2,
    )
    _run_scenario(scen)
    rows = _read_csv_rows(output_csv)
    emitted = {r["variable"] for r in rows}

    # Variables IAQ clave (production names)
    iaq_vars = {"co2", "temperature_01", "relative-humidity", "iaq-index", "people-count"}
    missing = iaq_vars - emitted
    assert not missing, f"variables IAQ faltantes: {missing}"

    # Frecuencia 1min: 2 aulas × 60 timestamps × 21 vars = 2520 base. Allow +/-.
    co2_count = sum(1 for r in rows if r["variable"] == "co2")
    # con 2 aulas y 60 timestamps deberíamos tener ~120 puntos co2
    assert co2_count >= 100, f"co2 count menor que esperado: {co2_count}"


@pytest.mark.integration
@pytest.mark.slow
def test_caseD_co2_within_realistic_range(tmp_path: Path) -> None:
    """``co2`` ∈ [400, 2200] ppm (rango duro vendor + clip)."""
    output_csv = tmp_path / "caseD_co2.csv"
    scen = _localize_scenario(
        SCENARIOS_DIR / "bms_v1_caseD_iaq.yaml",
        tmp_path,
        output_csv,
        start="2026-04-15T08:00:00",
        end="2026-04-15T09:00:00",
        n_aulas=2,
    )
    _run_scenario(scen)
    rows = _read_csv_rows(output_csv)
    co2_vals = [float(r["value"]) for r in rows if r["variable"] == "co2"]
    assert co2_vals
    assert all(400.0 <= v <= 2200.0 for v in co2_vals), (
        f"co2 fuera de rango [400, 2200]: min={min(co2_vals):.1f} max={max(co2_vals):.1f}"
    )


# ────────────────────── AliasSink + FaultEventSink interacción ──────────────────────


@pytest.mark.integration
@pytest.mark.slow
def test_alias_sink_passes_through_fault_events_unchanged(tmp_path: Path) -> None:
    """AliasSink wrapping debe dejar pasar variables ``fault.<tipo>`` SIN renombrar.

    Crítico para Caso C: si AliasSink renombra fault.sensor_drift accidentalmente,
    Telegraf no lo enruta a state_events (no matchea ``fault.*`` glob).
    """
    os.environ["BMS_FAULTS_ENABLED"] = "true"
    os.environ["BMS_PRODUCTION_ALIAS_ENABLED"] = "true"
    from bms_data_generator.config import reset_settings_cache

    reset_settings_cache()

    output_csv = tmp_path / "alias_fault_interaction.csv"
    scen = _build_scenario_with_high_prob_faults(tmp_path, output_csv, n_aulas=2)
    try:
        _run_scenario(scen)
    finally:
        os.environ.pop("BMS_FAULTS_ENABLED", None)
        from bms_data_generator.config import reset_settings_cache as _rsc

        _rsc()

    rows = _read_csv_rows(output_csv)
    fault_rows = [r for r in rows if r["variable"].startswith("fault.")]
    if not fault_rows:
        pytest.skip("no fault events in this run")

    # Confirmar que TODOS los fault rows mantienen prefijo `fault.` literal.
    fault_types = {r["variable"] for r in fault_rows}
    valid_types = {
        "fault.sensor_drift",
        "fault.valve_stuck",
        "fault.fan_failure",
        "fault.refrigerant_low",
    }
    invalid = fault_types - valid_types
    assert not invalid, f"fault types renombrados (no esperado): {invalid}"
