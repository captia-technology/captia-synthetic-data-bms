"""Domain adapter port — interface for domain-specific data generation."""
from __future__ import annotations

from typing import Any, Iterator, Protocol, runtime_checkable

import numpy as np
import pandas as pd

from ..core.models import DataPoint, Inventory


@runtime_checkable
class DomainAdapterPort(Protocol):
    """Port for domain-specific data generation.

    Ref: docs/specs/core-architecture.md Section 3.1
    """

    @property
    def domain_id(self) -> str: ...

    @property
    def version(self) -> str: ...

    def build_inventory(
        self, project_cfg: dict[str, Any], domain_cfg: dict[str, Any]
    ) -> Inventory: ...

    def build_context(
        self, time_index: pd.DatetimeIndex, project_cfg: dict[str, Any],
        domain_cfg: dict[str, Any], rng: np.random.Generator
    ) -> Any: ...

    def simulate(
        self, time_index: pd.DatetimeIndex, inventory: Inventory,
        ctx: Any, rng: np.random.Generator
    ) -> Iterator[DataPoint]: ...

    def validate_config(
        self, project_cfg: dict[str, Any], domain_cfg: dict[str, Any]
    ) -> list[str]: ...
