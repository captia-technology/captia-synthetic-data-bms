"""SeriesEngine — yields deterministic (ts, asset, variable) events.

Ref: docs/specs/core-architecture.md Section 2.2
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

import pandas as pd

from .models import Asset, Inventory, VariableDef


@dataclass(frozen=True)
class SeriesEvent:
    """Single event in the series iteration."""
    timestamp: pd.Timestamp
    asset: Asset
    variable_def: VariableDef


class SeriesEngine:
    """Yields series events from a time index and inventory."""

    def iterate(
        self,
        time_index: pd.DatetimeIndex,
        inventory: Inventory,
    ) -> Iterator[SeriesEvent]:
        """Yield (timestamp, asset, variable_def) for every point to generate."""
        for ts in time_index:
            for asset in inventory.assets:
                for var_def in asset.variables:
                    yield SeriesEvent(ts, asset, var_def)

    def count_total(self, time_index: pd.DatetimeIndex, inventory: Inventory) -> int:
        """Calculate total number of data points to generate."""
        total_vars = sum(len(a.variables) for a in inventory.assets)
        return len(time_index) * total_vars
