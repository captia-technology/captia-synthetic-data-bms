"""Auditoría estática de consistencia Telegraf routing ↔ catálogo de variables.

Cruza:
  - Variables con metric_kind ∈ {bool_state, setpoint_step} (que DEBEN ir a state_events).
  - Patrones suffix glob en ``processors.clone.tagpass.variable`` de telegraf.conf.

Falla si alguna variable on_change del catálogo NO matchea ningún glob → señal
silenciosa que se pierde en bucket telemetry en lugar de state_events.

Cierra L-PV-22 (routing on_change incompleto).
"""

from __future__ import annotations

import fnmatch
import tomllib
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
TELEGRAF_CONF = REPO_ROOT / "infra" / "telegraf" / "telegraf.conf"
VARIABLES_YAML = REPO_ROOT / "config" / "domains" / "bms_classrooms" / "variables.yaml"


def _load_telegraf_clone_globs() -> list[str]:
    with TELEGRAF_CONF.open("rb") as f:
        data = tomllib.load(f)
    clones = data.get("processors", {}).get("clone", [])
    assert clones, "no [[processors.clone]] block in telegraf.conf"
    # First clone block is the captia_point clone (state routing).
    return clones[0]["tagpass"]["variable"]


def _load_catalog_variables() -> list[dict]:
    with VARIABLES_YAML.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["asset_types"]["classroom"]["variables"]


def _match_any_glob(name: str, globs: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(name, g) for g in globs)


# ──────────────────── Tests ────────────────────


@pytest.mark.integration
def test_all_on_change_variables_match_telegraf_clone_tagpass() -> None:
    """Cada variable con metric_kind ∈ {bool_state, setpoint_step} matchea
    al menos un glob del clone tagpass.

    Si falla: la variable no se enrutaría a state_events, se quedaría en telemetry.
    """
    globs = _load_telegraf_clone_globs()
    catalog = _load_catalog_variables()

    on_change_vars = []
    for var in catalog:
        kind = var.get("metric_kind")
        # storage_mode explicit overrides metric_kind inference
        storage = var.get("storage_mode")
        is_on_change = (
            storage == "on_change" or
            (kind in {"bool_state", "setpoint_step"})
        )
        if is_on_change:
            # Use production_name if present (that's what gets emitted).
            emit_name = var.get("production_name") or var["name"]
            on_change_vars.append(emit_name)

    unmatched = [v for v in on_change_vars if not _match_any_glob(v, globs)]
    assert not unmatched, (
        f"on_change variables sin matchear ningún glob del Telegraf clone tagpass: {unmatched}\n"
        f"Globs disponibles: {globs}\n"
        f"→ Estas variables NO se enrutarán a state_events."
    )


@pytest.mark.integration
def test_continuous_variables_DO_NOT_match_clone_tagpass() -> None:
    """Variables continuous (analog_gauge, counter, bool_presence) NO deben
    matchear el clone tagpass — irían a state_events accidentalmente."""
    globs = _load_telegraf_clone_globs()
    catalog = _load_catalog_variables()

    continuous_vars = []
    for var in catalog:
        kind = var.get("metric_kind")
        storage = var.get("storage_mode")
        if storage == "on_change":
            continue
        if kind in {"analog_gauge", "counter", "bool_presence"}:
            emit_name = var.get("production_name") or var["name"]
            continuous_vars.append((emit_name, kind))

    leaks = [(name, kind) for (name, kind) in continuous_vars if _match_any_glob(name, globs)]
    # Aceptamos ciertos leaks documentados (ej. valve_control es analog_gauge en
    # el modelo pero metric_kind on_change semánticamente — está en el glob para
    # alinear con producción).
    accepted_leaks = {"valve_control"}  # See L-PV-22 notes.
    unexpected = [(n, k) for (n, k) in leaks if n not in accepted_leaks]
    assert not unexpected, (
        f"variables continuous matcheando clone tagpass (irían a state_events accidentalmente): "
        f"{unexpected}\nGlobs: {globs}"
    )


@pytest.mark.integration
def test_telegraf_clone_includes_fault_glob() -> None:
    """``fault.*`` debe estar en el clone tagpass para que FaultEventEmitter funcione."""
    globs = _load_telegraf_clone_globs()
    assert "fault.*" in globs, (
        "fault.* glob ausente del Telegraf clone tagpass — los FaultEvents NO se enrutarían a state_events"
    )


@pytest.mark.integration
def test_telegraf_has_two_mqtt_consumers() -> None:
    """T-PV-18: Telegraf debe tener 2 mqtt_consumer (telemetry + event)."""
    with TELEGRAF_CONF.open("rb") as f:
        data = tomllib.load(f)
    consumers = data.get("inputs", {}).get("mqtt_consumer", [])
    assert len(consumers) == 2, f"esperado 2 mqtt_consumer, got {len(consumers)}"

    # Identify by topics
    telemetry_topics = consumers[0]["topics"]
    event_topics = consumers[1]["topics"]
    assert any("telemetry" in t for t in telemetry_topics), \
        f"primer mqtt_consumer no escucha telemetry topics: {telemetry_topics}"
    assert any("event" in t for t in event_topics), \
        f"segundo mqtt_consumer no escucha event topics: {event_topics}"


@pytest.mark.integration
def test_telegraf_has_three_influxdb_outputs() -> None:
    """T-PV-18: Telegraf debe tener 3 outputs InfluxDB v2 (telemetry, state_events, telemetry_events)."""
    with TELEGRAF_CONF.open("rb") as f:
        data = tomllib.load(f)
    outputs = data.get("outputs", {}).get("influxdb_v2", [])
    assert len(outputs) == 3, f"esperado 3 influxdb_v2 outputs, got {len(outputs)}"

    buckets = []
    for o in outputs:
        bucket_str = o.get("bucket", "")
        # Extract default from "${VAR:-default}" pattern
        if ":-" in bucket_str:
            buckets.append(bucket_str.split(":-")[1].rstrip("}"))
        else:
            buckets.append(bucket_str)
    assert "telemetry" in buckets
    assert "state_events" in buckets
    assert "telemetry_events" in buckets


@pytest.mark.integration
def test_telegraf_outputs_have_correct_namepass() -> None:
    """Cada output filtra el measurement correcto via namepass."""
    with TELEGRAF_CONF.open("rb") as f:
        data = tomllib.load(f)
    outputs = data.get("outputs", {}).get("influxdb_v2", [])

    expected_pairings = {
        "telemetry": "captia_point",
        "state_events": "captia_point_state",
        "telemetry_events": "captia_cmd_event",
    }
    for o in outputs:
        bucket_str = o.get("bucket", "")
        if ":-" in bucket_str:
            bucket = bucket_str.split(":-")[1].rstrip("}")
        else:
            bucket = bucket_str
        namepass = o.get("namepass", [])
        expected_measurement = expected_pairings.get(bucket)
        if expected_measurement is None:
            continue
        assert expected_measurement in namepass, (
            f"output→{bucket} debería tener namepass=[{expected_measurement!r}], got {namepass}"
        )


@pytest.mark.integration
def test_telegraf_dedup_only_targets_state_clone() -> None:
    """``processors.dedup`` solo afecta a captia_point_state (no debe deduplicar telemetry raw)."""
    with TELEGRAF_CONF.open("rb") as f:
        data = tomllib.load(f)
    dedups = data.get("processors", {}).get("dedup", [])
    assert dedups, "no [[processors.dedup]] block found"
    for d in dedups:
        namepass = d.get("namepass", [])
        assert "captia_point_state" in namepass, (
            f"dedup namepass={namepass} — debe incluir captia_point_state"
        )
        assert "captia_point" not in namepass, (
            f"dedup namepass={namepass} — NO debe incluir captia_point (rompería rate raw)"
        )
