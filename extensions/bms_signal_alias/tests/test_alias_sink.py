"""Tests para AliasSinkAdapter."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from bms_signal_alias import AliasSinkAdapter, build_alias_map_from_yaml


@dataclass
class FakeDataPoint:
    asset_id: str
    variable: str
    value: float


class FakeSink:
    def __init__(self):
        self.emitted = []
        self.opened = False
        self.closed = False
        self.flushed = 0

    def open(self):
        self.opened = True

    def close(self):
        self.closed = True

    def flush(self):
        self.flushed += 1

    def emit(self, point):
        self.emitted.append(point)

    def emit_batch(self, points):
        for p in points:
            self.emitted.append(p)


# ─────────────────────────── build_alias_map ──────────────────────────────


def test_build_alias_map_from_vendor_format(tmp_path: Path) -> None:
    yaml_file = tmp_path / "variables.yaml"
    yaml_file.write_text(
        """
asset_types:
  classroom:
    variables:
      - name: temperature
        production_name: temperature_01
        unit: "°C"
      - name: humidity
        production_name: relative-humidity
      - name: co2
        production_name: co2
      - name: noise
""",
        encoding="utf-8",
    )
    aliases = build_alias_map_from_yaml(yaml_file)
    assert aliases == {
        "temperature": "temperature_01",
        "humidity": "relative-humidity",
    }


def test_build_alias_map_skips_when_prod_equals_name(tmp_path: Path) -> None:
    yaml_file = tmp_path / "variables.yaml"
    yaml_file.write_text(
        """
asset_types:
  classroom:
    variables:
      - name: co2
        production_name: co2
""",
        encoding="utf-8",
    )
    assert build_alias_map_from_yaml(yaml_file) == {}


def test_build_alias_map_handles_empty_yaml(tmp_path: Path) -> None:
    yaml_file = tmp_path / "variables.yaml"
    yaml_file.write_text("", encoding="utf-8")
    assert build_alias_map_from_yaml(yaml_file) == {}


def test_build_alias_map_real_repo_yaml() -> None:
    """Smoke: verify that the production override in the repo loads correctly."""
    repo_yaml = (
        Path(__file__).resolve().parents[3]
        / "config"
        / "domains"
        / "bms_classrooms"
        / "variables.yaml"
    )
    if not repo_yaml.exists():
        pytest.skip(f"Repo yaml not found at {repo_yaml}")
    aliases = build_alias_map_from_yaml(repo_yaml)
    # Sanity checks against expected production names
    assert aliases["temperature"] == "temperature_01"
    assert aliases["humidity"] == "relative-humidity"
    assert aliases["power"] == "power_01"
    assert aliases["thermostat_setpoint"] == "temperature_01_sp"
    assert aliases["hvac_mode"] == "ac_control"
    assert aliases["hvac_enable"] == "ac_state"
    assert aliases["heating_valve_pos"] == "valve_control"
    assert aliases["relay_1"] == "light_01_state"
    assert aliases["presence_pir"] == "occupancy"  # bool semantic alias
    assert aliases["occupancy"] == "people-count"  # int alias
    # co2 NOT in map (production_name == name)
    assert "co2" not in aliases


# ────────────────────────── AliasSinkAdapter ────────────────────────────


def test_alias_sink_renames_known_variables() -> None:
    sink = FakeSink()
    adapter = AliasSinkAdapter(sink, {"temperature": "temperature_01", "power": "power_01"})

    p1 = FakeDataPoint("AULA01", "temperature", 22.5)
    p2 = FakeDataPoint("AULA01", "power", 350.0)
    adapter.emit(p1)
    adapter.emit(p2)

    assert sink.emitted[0].variable == "temperature_01"
    assert sink.emitted[1].variable == "power_01"
    assert adapter.renamed_count == 2
    assert adapter.passthrough_count == 0


def test_alias_sink_passthrough_unknown() -> None:
    sink = FakeSink()
    adapter = AliasSinkAdapter(sink, {"temperature": "temperature_01"})

    p = FakeDataPoint("AULA01", "humidity", 55.0)  # not in alias map
    adapter.emit(p)

    assert sink.emitted[0].variable == "humidity"
    assert adapter.renamed_count == 0
    assert adapter.passthrough_count == 1


def test_alias_sink_does_not_mutate_original() -> None:
    sink = FakeSink()
    adapter = AliasSinkAdapter(sink, {"temperature": "temperature_01"})
    p = FakeDataPoint("AULA01", "temperature", 22.5)
    adapter.emit(p)
    # original retains vendor name
    assert p.variable == "temperature"
    # emitted is a separate dataclass instance with new name
    assert sink.emitted[0].variable == "temperature_01"
    assert sink.emitted[0] is not p


def test_alias_sink_emit_batch_uses_real_sink_batch_when_available() -> None:
    sink = FakeSink()
    adapter = AliasSinkAdapter(sink, {"power": "power_01"})
    points = [
        FakeDataPoint("AULA01", "power", 100.0),
        FakeDataPoint("AULA01", "power", 200.0),
        FakeDataPoint("AULA01", "co2", 500.0),
    ]
    adapter.emit_batch(points)
    assert [p.variable for p in sink.emitted] == ["power_01", "power_01", "co2"]
    assert adapter.renamed_count == 2
    assert adapter.passthrough_count == 1


def test_alias_sink_lifecycle() -> None:
    sink = FakeSink()
    adapter = AliasSinkAdapter(sink, {})
    adapter.open()
    adapter.flush()
    adapter.close()
    assert sink.opened is True
    assert sink.flushed == 1
    assert sink.closed is True


def test_alias_sink_from_yaml(tmp_path: Path) -> None:
    yaml_file = tmp_path / "variables.yaml"
    yaml_file.write_text(
        """
asset_types:
  classroom:
    variables:
      - name: temperature
        production_name: temperature_01
""",
        encoding="utf-8",
    )
    sink = FakeSink()
    adapter = AliasSinkAdapter.from_yaml(sink, yaml_file)
    assert adapter.aliases == {"temperature": "temperature_01"}


def test_alias_sink_handles_sink_without_optional_methods() -> None:
    """Sink without open/close/flush/emit_batch should still work."""

    class MinimalSink:
        def __init__(self):
            self.emitted = []

        def emit(self, p):
            self.emitted.append(p)

    sink = MinimalSink()
    adapter = AliasSinkAdapter(sink, {"power": "power_01"})
    adapter.open()  # no-op
    adapter.flush()  # no-op
    adapter.emit_batch([FakeDataPoint("AULA01", "power", 100.0)])
    adapter.close()  # no-op
    assert sink.emitted[0].variable == "power_01"
