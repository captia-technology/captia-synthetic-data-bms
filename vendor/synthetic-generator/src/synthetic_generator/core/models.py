"""Core data models for multi-domain synthetic data generation."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class DataType(str, Enum):
    FLOAT = "float"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    STRING = "string"
    ENUM = "enum"


class PointType(str, Enum):
    SENSOR = "sensor"
    ACTUATOR = "actuator"
    SETPOINT = "setpoint"
    CALCULATED = "calculated"


class MetricKind(str, Enum):
    """Logical signal type that determines downsampling policy.

    Defined explicitly per variable in config/domains/<domain>/variables.yaml.
    Used by Flux Tasks to select the correct rollup strategy.

    Values:
        analog_gauge    → rollup: mean, min, max
        bool_presence   → rollup: duty, count_rise, last
        bool_state      → rollup: last, duty, count_rise
        setpoint_step   → event bucket: changes_only
        counter         → rollup: sum (via difference for cumulative_monotonic)
        skip            → no rollup (strings, context fields)
    """
    ANALOG_GAUGE = "analog_gauge"
    BOOL_PRESENCE = "bool_presence"
    BOOL_STATE = "bool_state"
    SETPOINT_STEP = "setpoint_step"
    COUNTER = "counter"
    SKIP = "skip"


class CounterWire(str, Enum):
    """How a counter signal is wired — determines Flux aggregation strategy.

    Values:
        cumulative_monotonic → value grows monotonically, need difference(nonNegative:true)
        delta_already        → value already represents delta per sample, just sum()
    """
    CUMULATIVE_MONOTONIC = "cumulative_monotonic"
    DELTA_ALREADY = "delta_already"


class Quality(str, Enum):
    OK = "OK"
    MISSING = "MISSING"
    OUTLIER = "OUTLIER"
    INTERPOLATED = "INTERPOLATED"
    SUSPECT = "SUSPECT"


@dataclass(frozen=True)
class VariableDef:
    name: str
    data_type: DataType = DataType.FLOAT
    unit: str = ""
    point_type: PointType = PointType.SENSOR
    category: str = ""
    expected_range_soft: Optional[tuple[float, float]] = None
    expected_range_hard: Optional[tuple[float, float]] = None
    is_optional: bool = False
    metric_kind: MetricKind = MetricKind.SKIP
    counter_wire: Optional[CounterWire] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.name != self.name.lower():
            object.__setattr__(self, 'name', self.name.lower())


@dataclass(frozen=True)
class Asset:
    asset_id: str
    asset_type: str
    variables: tuple[VariableDef, ...] = field(default_factory=tuple)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.asset_id != self.asset_id.upper():
            object.__setattr__(self, 'asset_id', self.asset_id.upper())


@dataclass
class Inventory:
    domain_id: str
    assets: list[Asset] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def get_asset(self, asset_id: str) -> Optional[Asset]:
        for asset in self.assets:
            if asset.asset_id == asset_id.upper():
                return asset
        return None

    def list_asset_ids(self) -> list[str]:
        return [a.asset_id for a in self.assets]

    def list_variables(self, asset_id: str) -> list[str]:
        asset = self.get_asset(asset_id)
        if asset:
            return [v.name for v in asset.variables]
        return []


@dataclass
class DataPoint:
    timestamp: datetime
    domain_id: str
    site_id: str
    asset_id: str
    variable: str
    value: Any
    unit: str
    data_type: DataType
    point_type: PointType
    quality: Quality = Quality.OK
    origin: str = "synthetic"
    pvn: str = ""
    pvp: str = ""

    def __post_init__(self):
        if self.asset_id != self.asset_id.upper():
            self.asset_id = self.asset_id.upper()
        if self.variable != self.variable.lower():
            self.variable = self.variable.lower()


@dataclass
class SimulationContext:
    time_index: Any  # pd.DatetimeIndex
    rng: Any  # np.random.Generator
    metadata: dict[str, Any] = field(default_factory=dict)
