"""RateController — token-bucket rate limiter with perturbation injection.

Ref: docs/specs/core-architecture.md Section 2.5
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Iterator

import numpy as np

from .models import DataPoint
from .clock import ClockPort, SystemClock


@dataclass
class RateConfig:
    points_per_second: float = 10.0
    jitter_ms: float = 0.0
    duplicate_probability: float = 0.0
    out_of_order_probability: float = 0.0
    gap_probability: float = 0.0
    gap_duration_points: tuple[int, int] = (1, 5)


@dataclass
class EmitEvent:
    point: DataPoint
    delay_ms: float = 0.0
    is_duplicate: bool = False
    is_gap: bool = False


class RateController:
    """Token-bucket rate limiter with perturbation injection."""

    def __init__(self, config: RateConfig, rng: np.random.Generator,
                 clock: ClockPort | None = None):
        self.config = config
        self.rng = rng
        self.clock = clock or SystemClock()
        self._gap_remaining = 0

    def pace(self, batch: list[DataPoint]) -> Iterator[EmitEvent]:
        """Apply rate limiting and perturbations to a batch."""
        points = list(batch)

        # Out-of-order: shuffle a portion
        if self.config.out_of_order_probability > 0:
            for i in range(len(points) - 1):
                if self.rng.random() < self.config.out_of_order_probability:
                    j = min(i + self.rng.integers(1, 4), len(points) - 1)
                    points[i], points[j] = points[j], points[i]

        for point in points:
            # Gap handling
            if self._gap_remaining > 0:
                self._gap_remaining -= 1
                yield EmitEvent(point=point, is_gap=True)
                continue

            # Start new gap?
            if self.config.gap_probability > 0 and self.rng.random() < self.config.gap_probability:
                lo, hi = self.config.gap_duration_points
                self._gap_remaining = int(self.rng.integers(lo, hi + 1))
                yield EmitEvent(point=point, is_gap=True)
                continue

            # Jitter
            delay_ms = 0.0
            if self.config.jitter_ms > 0:
                delay_ms = self.rng.uniform(0, self.config.jitter_ms)

            yield EmitEvent(point=point, delay_ms=delay_ms)

            # Duplicate
            if self.config.duplicate_probability > 0 and self.rng.random() < self.config.duplicate_probability:
                yield EmitEvent(point=point, delay_ms=delay_ms, is_duplicate=True)

    def wait_for_interval(self, elapsed_seconds: float) -> None:
        """Sleep for remaining interval time."""
        if self.config.points_per_second <= 0:
            return
        interval = 1.0 / self.config.points_per_second
        remaining = interval - elapsed_seconds
        if remaining > 0:
            self.clock.sleep(remaining)
