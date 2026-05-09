"""Shared test fixtures for synthetic data generator."""
from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pytest

from synthetic_generator.core.models import (
    Asset,
    DataPoint,
    DataType,
    Inventory,
    PointType,
    Quality,
    VariableDef,
)
from synthetic_generator.core.config import (
    AnomalyConfig,
    DomainReference,
    OutputConfig,
    PhasesConfig,
    ProjectConfig,
    ScenarioConfig,
    SimulationConfig,
    SinkConfig,
    SinkType,
)


SEED = 42


@pytest.fixture
def rng():
    """Deterministic random generator."""
    return np.random.default_rng(seed=SEED)


@pytest.fixture
def seed():
    return SEED


@pytest.fixture
def short_time_index():
    """24-hour time index at 5min freq."""
    return pd.date_range(
        start="2026-01-01",
        end="2026-01-01 23:55",
        freq="5min",
        tz="Europe/Madrid",
    )


@pytest.fixture
def week_time_index():
    """7-day time index at 5min freq."""
    return pd.date_range(
        start="2026-01-01",
        end="2026-01-07 23:55",
        freq="5min",
        tz="Europe/Madrid",
    )


@pytest.fixture
def sample_variable_def():
    """Single VariableDef fixture."""
    return VariableDef(
        name="temperature",
        data_type=DataType.FLOAT,
        unit="°C",
        point_type=PointType.SENSOR,
        expected_range_soft=(15.0, 30.0),
        expected_range_hard=(5.0, 45.0),
    )


@pytest.fixture
def sample_asset(sample_variable_def):
    """Single Asset fixture with one variable."""
    return Asset(
        asset_id="AULA01",
        asset_type="classroom",
        variables=(sample_variable_def,),
    )


@pytest.fixture
def sample_inventory(sample_asset):
    """Minimal inventory with one asset."""
    return Inventory(
        domain_id="test_domain",
        assets=[sample_asset],
        metadata={"site_id": "test_site"},
    )


@pytest.fixture
def multi_asset_inventory():
    """Inventory with 3 assets and 3 variables each."""
    assets = []
    for i in range(3):
        variables = tuple(
            VariableDef(
                name=f"var_{j}",
                data_type=DataType.FLOAT,
                unit="unit",
                expected_range_hard=(0.0, 100.0),
            )
            for j in range(3)
        )
        assets.append(
            Asset(
                asset_id=f"ASSET{i:02d}",
                asset_type="test",
                variables=variables,
            )
        )
    return Inventory(domain_id="test", assets=assets)


@pytest.fixture
def sample_data_point():
    """Single DataPoint fixture."""
    return DataPoint(
        timestamp=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
        domain_id="test_domain",
        site_id="test_site",
        asset_id="AULA01",
        variable="temperature",
        value=22.5,
        unit="°C",
        data_type=DataType.FLOAT,
        point_type=PointType.SENSOR,
        quality=Quality.OK,
        origin="synthetic",
        pvn="AULA01__temperature",
    )


@pytest.fixture
def minimal_scenario_config():
    """Minimal valid ScenarioConfig."""
    return ScenarioConfig(
        project=ProjectConfig(namespace="test", site_id="test_site"),
        simulation=SimulationConfig(
            start="2026-01-01",
            end="2026-01-01",
            freq="5min",
            seed=42,
        ),
        domain=DomainReference(id="bms_classrooms"),
        sinks=[SinkConfig(type=SinkType.FILE, config={"path": "outputs/test.csv", "format": "csv_long"})],
    )


@pytest.fixture
def empty_inventory():
    """Inventory with zero assets."""
    return Inventory(domain_id="empty", assets=[])
