"""Unit tests for scenario configuration."""
from pathlib import Path
import tempfile

import pytest
import yaml

from synthetic_generator.core.config import (
    AnomalyConfig,
    BackfillPhase,
    DomainReference,
    LivePhase,
    OutputConfig,
    PhasesConfig,
    PerturbationsConfig,
    ProjectConfig,
    ScenarioConfig,
    SimulationConfig,
    SinkConfig,
    SinkType,
    load_scenario_config,
)


class TestScenarioConfig:
    def test_minimal_valid(self, minimal_scenario_config):
        cfg = minimal_scenario_config
        assert cfg.project.namespace == "test"
        assert cfg.simulation.seed == 42
        assert cfg.domain.id == "bms_classrooms"

    def test_defaults(self):
        cfg = ScenarioConfig(
            project=ProjectConfig(namespace="x", site_id="s"),
            simulation=SimulationConfig(start="2026-01-01", end="2026-01-02"),
            domain=DomainReference(id="test"),
        )
        assert cfg.simulation.freq == "5min"
        assert cfg.simulation.timezone == "Europe/Madrid"
        assert cfg.phases.backfill.enabled is True
        assert cfg.phases.live.enabled is False
        assert cfg.anomalies.p_missing == 0.0
        assert cfg.anomalies.p_outlier == 0.0
        assert cfg.perturbations.jitter_ms == 0.0
        assert cfg.output.format == "long"

    def test_seed_constraint(self):
        with pytest.raises(Exception):
            SimulationConfig(start="2026-01-01", end="2026-01-02", seed=-1)


class TestSinkConfig:
    def test_mqtt_type(self):
        cfg = SinkConfig(type=SinkType.MQTT, config={"broker_url": "tcp://localhost:1883"})
        assert cfg.type == SinkType.MQTT

    def test_file_type(self):
        cfg = SinkConfig(type=SinkType.FILE, config={"path": "out.csv", "format": "csv_long"})
        assert cfg.type == SinkType.FILE

    def test_stdout_type(self):
        cfg = SinkConfig(type=SinkType.STDOUT)
        assert cfg.config == {}


class TestLoadScenarioConfig:
    def test_load_valid_yaml(self, tmp_path):
        config = {
            "project": {"namespace": "test", "site_id": "s1"},
            "simulation": {"start": "2026-01-01", "end": "2026-01-02", "seed": 42},
            "domain": {"id": "bms_classrooms"},
            "sinks": [{"type": "file", "config": {"path": "out.csv"}}],
        }
        p = tmp_path / "test.yaml"
        p.write_text(yaml.dump(config), encoding="utf-8")
        loaded = load_scenario_config(p)
        assert loaded.project.namespace == "test"
        assert loaded.simulation.seed == 42

    def test_load_with_anomalies(self, tmp_path):
        config = {
            "project": {"namespace": "t", "site_id": "s"},
            "simulation": {"start": "2026-01-01", "end": "2026-01-02"},
            "domain": {"id": "d"},
            "anomalies": {"p_missing": 0.05, "p_outlier": 0.02},
        }
        p = tmp_path / "anom.yaml"
        p.write_text(yaml.dump(config), encoding="utf-8")
        loaded = load_scenario_config(p)
        assert loaded.anomalies.p_missing == 0.05
        assert loaded.anomalies.p_outlier == 0.02


class TestPerturbationsConfig:
    def test_defaults(self):
        p = PerturbationsConfig()
        assert p.jitter_ms == 0.0
        assert p.duplicate_probability == 0.0
        assert p.out_of_order_probability == 0.0
        assert p.gap_probability == 0.0

    def test_gap_duration_range(self):
        p = PerturbationsConfig(gap_duration_points=(2, 10))
        assert p.gap_duration_points == (2, 10)
