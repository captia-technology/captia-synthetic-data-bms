"""ValueEngine — delegates value generation to domain adapter.

Ref: docs/specs/core-architecture.md Section 2.3
"""
from __future__ import annotations

from typing import Any

import numpy as np

from ..ports.domain import DomainAdapterPort
from .series import SeriesEvent


class ValueEngine:
    """Generates values by delegating to domain adapter."""

    def generate(
        self,
        domain_adapter: DomainAdapterPort,
        context: Any,
        series_event: SeriesEvent,
        rng: np.random.Generator,
    ) -> Any:
        """Generate a single value for a series event.

        Note: In Phase 1, we use the domain's monolithic simulate() method
        instead of fine-grained generate_value(). This class is provided
        for Phase 2+ usage.
        """
        if hasattr(domain_adapter, 'generate_value'):
            return domain_adapter.generate_value(context, series_event, rng)
        raise NotImplementedError(
            "Domain adapter does not support fine-grained generate_value(). "
            "Use simulate() instead (Phase 1 approach)."
        )
