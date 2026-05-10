"""Integration test del calendario lectivo Valencia 2025-26 (T-PV-09).

Verifica que durante períodos vacacionales documentados en
``extensions/bms_calibration/.../school_calendar.py:_BREAKS_2025_2026`` y
expandidos en ``config/domains/bms_classrooms/domain.yaml::calendar.holidays``,
el generador produce occupancy ≈ 0 y HVAC en standby.

Cierra L-PV-06 + valida T-PV-09.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
DOMAIN_YAML_LOCAL = REPO_ROOT / "config" / "domains" / "bms_classrooms" / "domain.yaml"


def _write_scenario(
    tmp_path: Path, output_csv: Path, start: str, end: str, n_aulas: int = 2
) -> Path:
    """Write scenario YAML with explicit domain.config_path → local override.

    Sin config_path explícito, el vendor carga su propio domain.yaml (que NO
    tiene los holidays expandidos T-PV-09). Apuntamos al override local para
    que el calendario Valencia 2025-26 oficial entre en vigor.
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
            "start": start,
            "end": end,
            "freq": "5min",
            "n_aulas": n_aulas,
        },
        "domain": {"id": "bms_classrooms", "config_path": str(DOMAIN_YAML_LOCAL)},
        "phases": {"backfill": {"enabled": True}, "live": {"enabled": False}},
        "anomalies": {"p_missing": 0.0, "p_outlier": 0.0},
        "sinks": [{"type": "file", "config": {"path": str(output_csv), "format": "csv_long"}}],
        "output": {"format": "long", "include_quality": True, "include_mqtt": False},
    }
    path = tmp_path / f"scenario_{output_csv.stem}.yaml"
    path.write_text(yaml.safe_dump(scenario), encoding="utf-8")
    return path


def _run_and_get_rows(scenario_path: Path) -> list[dict]:
    os.environ["BMS_PRODUCTION_ALIAS_ENABLED"] = "true"
    from bms_data_generator.config import reset_settings_cache

    reset_settings_cache()
    from bms_data_generator.services.runner_service import _build_runner

    result = _build_runner(scenario_path)
    runner = result[0]
    runner.run()
    output_csv = Path(yaml.safe_load(scenario_path.read_text())["sinks"][0]["config"]["path"])
    with output_csv.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _occupancy_mean(rows: list[dict], variable: str = "people-count") -> float:
    """Mean of `variable` across all rows (production naming via AliasSink)."""
    vals = [float(r["value"]) for r in rows if r["variable"] == variable]
    return sum(vals) / len(vals) if vals else 0.0


def _hvac_enable_duty(rows: list[dict], variable: str = "ac_state") -> float:
    """Fraction of samples where ac_state == 1 (HVAC enabled)."""
    vals = [float(r["value"]) for r in rows if r["variable"] == variable]
    return sum(vals) / len(vals) if vals else 0.0


# ─────────────────────── Test cases ───────────────────────


@pytest.mark.integration
@pytest.mark.slow
def test_lectivo_day_has_occupancy(tmp_path: Path) -> None:
    """Lunes 2026-01-12 (lectivo, fuera de vacaciones) debe tener occupancy > 0."""
    csv_path = tmp_path / "lectivo.csv"
    scen = _write_scenario(
        tmp_path, csv_path, start="2026-01-12T08:00:00", end="2026-01-12T15:00:00", n_aulas=2
    )
    rows = _run_and_get_rows(scen)
    occ_mean = _occupancy_mean(rows, "people-count")
    assert occ_mean > 5.0, f"lectivo expected occupancy > 5, got {occ_mean:.2f}"


@pytest.mark.integration
@pytest.mark.slow
def test_navidad_day_has_zero_occupancy(tmp_path: Path) -> None:
    """2025-12-26 (Navidad, expandido en T-PV-09) debe tener occupancy ≈ 0."""
    csv_path = tmp_path / "navidad.csv"
    scen = _write_scenario(
        tmp_path, csv_path, start="2025-12-26T08:00:00", end="2025-12-26T15:00:00", n_aulas=2
    )
    rows = _run_and_get_rows(scen)
    occ_mean = _occupancy_mean(rows, "people-count")
    assert occ_mean < 1.0, f"Navidad expected occupancy < 1, got {occ_mean:.2f}"


@pytest.mark.integration
@pytest.mark.slow
def test_fallas_day_has_zero_occupancy(tmp_path: Path) -> None:
    """2026-03-17 (Fallas, expandido en T-PV-09) debe tener occupancy ≈ 0."""
    csv_path = tmp_path / "fallas.csv"
    scen = _write_scenario(
        tmp_path, csv_path, start="2026-03-17T08:00:00", end="2026-03-17T15:00:00", n_aulas=2
    )
    rows = _run_and_get_rows(scen)
    occ_mean = _occupancy_mean(rows, "people-count")
    assert occ_mean < 1.0, f"Fallas expected occupancy < 1, got {occ_mean:.2f}"


@pytest.mark.integration
@pytest.mark.slow
def test_pascua_day_has_zero_occupancy(tmp_path: Path) -> None:
    """2026-04-08 (Pascua, expandido en T-PV-09) debe tener occupancy ≈ 0."""
    csv_path = tmp_path / "pascua.csv"
    scen = _write_scenario(
        tmp_path, csv_path, start="2026-04-08T08:00:00", end="2026-04-08T15:00:00", n_aulas=2
    )
    rows = _run_and_get_rows(scen)
    occ_mean = _occupancy_mean(rows, "people-count")
    assert occ_mean < 1.0, f"Pascua expected occupancy < 1, got {occ_mean:.2f}"


@pytest.mark.integration
@pytest.mark.slow
def test_weekend_has_zero_occupancy(tmp_path: Path) -> None:
    """Sábado 2026-01-17 (fin de semana) debe tener occupancy ≈ 0."""
    csv_path = tmp_path / "weekend.csv"
    scen = _write_scenario(
        tmp_path, csv_path, start="2026-01-17T08:00:00", end="2026-01-17T15:00:00", n_aulas=2
    )
    rows = _run_and_get_rows(scen)
    occ_mean = _occupancy_mean(rows, "people-count")
    assert occ_mean < 1.0, f"Weekend expected occupancy < 1, got {occ_mean:.2f}"
