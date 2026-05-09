"""Scenario configuration with Pydantic validation."""
from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Literal, Optional

import yaml
from pydantic import BaseModel, Field


class ProjectConfig(BaseModel):
    namespace: str = Field(..., description="Project namespace")
    site_id: str = Field(..., description="Site identifier")
    modo: str = Field(default="synthetic")
    schema_version: str = Field(default="v0.1")


class SimulationConfig(BaseModel):
    timezone: str = Field(default="Europe/Madrid")
    seed: int = Field(default=42, ge=0)
    start: str = Field(..., description="ISO date: YYYY-MM-DD")
    end: str = Field(..., description="ISO date")
    freq: str = Field(default="5min")


class DomainReference(BaseModel):
    id: str = Field(..., description="Registered domain_id")
    config_path: Optional[str] = Field(default=None)


class BackfillPhase(BaseModel):
    enabled: bool = Field(default=True)


class LivePhase(BaseModel):
    enabled: bool = Field(default=False)
    rate_points_per_sec: float = Field(default=10.0, gt=0)
    lookahead_hours: int = Field(default=24, ge=1)
    regenerate_on_exhaustion: bool = Field(default=True)


class PhasesConfig(BaseModel):
    backfill: BackfillPhase = Field(default_factory=BackfillPhase)
    live: LivePhase = Field(default_factory=LivePhase)


class PerturbationsConfig(BaseModel):
    jitter_ms: float = Field(default=0.0, ge=0)
    duplicate_probability: float = Field(default=0.0, ge=0, le=1)
    out_of_order_probability: float = Field(default=0.0, ge=0, le=1)
    gap_probability: float = Field(default=0.0, ge=0, le=1)
    gap_duration_points: tuple[int, int] = Field(default=(1, 5))


class AnomalyConfig(BaseModel):
    p_missing: float = Field(default=0.0, ge=0, le=1)
    p_outlier: float = Field(default=0.0, ge=0, le=1)
    burst_missing_prob_per_day: float = Field(default=0.0, ge=0, le=1)
    burst_duration_range: tuple[int, int] = Field(default=(2, 18))


class SinkType(str, Enum):
    MQTT = "mqtt"
    FILE = "file"
    STDOUT = "stdout"


class SinkConfig(BaseModel):
    type: SinkType
    config: dict[str, Any] = Field(default_factory=dict)


class OutputConfig(BaseModel):
    format: Literal["long", "wide"] = "long"
    include_quality: bool = True
    include_mqtt: bool = True


class ScenarioConfig(BaseModel):
    """Top-level scenario configuration."""
    project: ProjectConfig
    simulation: SimulationConfig
    domain: DomainReference
    phases: PhasesConfig = Field(default_factory=PhasesConfig)
    perturbations: PerturbationsConfig = Field(default_factory=PerturbationsConfig)
    anomalies: AnomalyConfig = Field(default_factory=AnomalyConfig)
    sinks: list[SinkConfig] = Field(default_factory=list)
    output: OutputConfig = Field(default_factory=OutputConfig)


def load_scenario_config(path: Path) -> ScenarioConfig:
    """Load and validate scenario config from YAML."""
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    # Try new format first
    try:
        return ScenarioConfig(**raw)
    except Exception:
        # Try legacy format conversion
        return _convert_legacy(raw)


def _convert_legacy(raw: dict[str, Any]) -> ScenarioConfig:
    """Convert legacy project YAML to ScenarioConfig."""
    project = raw.get("project", {})
    simulation = raw.get("simulation", {})
    domain = raw.get("domain", {})
    anomalies = raw.get("anomalies", {})
    output = raw.get("output", {})

    # Build sinks from legacy mqtt/output sections
    sinks = raw.get("sinks", [])
    if not sinks:
        mqtt_cfg = raw.get("mqtt", {})
        if mqtt_cfg:
            sinks.append({"type": "mqtt", "config": mqtt_cfg})
        if output.get("path") or output.get("format"):
            sinks.append({"type": "file", "config": {"path": output.get("path", "outputs/dataset.csv"), "format": output.get("format", "csv_long")}})

        return ScenarioConfig(
        project=ProjectConfig(**project) if project else ProjectConfig(namespace="captia", site_id="default"),
        simulation=SimulationConfig(**{k: v for k, v in simulation.items() if k in SimulationConfig.model_fields}),
        domain=DomainReference(**domain),
        anomalies=AnomalyConfig(**{k: v for k, v in anomalies.items() if k in AnomalyConfig.model_fields}) if anomalies else AnomalyConfig(),
        sinks=[SinkConfig(**s) for s in sinks],
        output=OutputConfig(**{k: v for k, v in output.items() if k in OutputConfig.model_fields}) if output else OutputConfig(),
        phases=PhasesConfig(**raw.get("phases", {})) if "phases" in raw else PhasesConfig(),
        perturbations=PerturbationsConfig(**raw.get("perturbations", {})) if "perturbations" in raw else PerturbationsConfig(),
    )
