"""Anomaly injection engine for synthetic data."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

import numpy as np

from .models import DataPoint, Quality


@dataclass
class AnomalyConfig:
    """Configuration for anomaly injection."""
    p_missing: float = 0.0
    p_outlier: float = 0.0
    burst_missing_prob_per_day: float = 0.0
    burst_duration_range: tuple[int, int] = (2, 18)


class AnomalyEngine:
    """Post-processing engine that injects anomalies into data streams.

    Supports:
    - Random missing values (p_missing)
    - Random outliers (p_outlier)
    - Burst missing events (multi-point gaps)
    """

    def __init__(self, config: AnomalyConfig, rng: np.random.Generator):
        self.config = config
        self.rng = rng
        self._burst_active = False
        self._burst_counter = 0
        self._points_since_last_burst = 0
        self._points_per_day = 288  # 5min freq = 288 points/day

    def apply(self, points: Iterator[DataPoint]) -> Iterator[DataPoint]:
        """Apply anomaly injection to a stream of data points.

        Args:
            points: Iterator of data points

        Yields:
            Modified data points (missing values are filtered out)
        """
        for point in points:
            modified = self.process(point)
            if modified is not None:
                yield modified

    def process(self, point: DataPoint) -> DataPoint | None:
        """Process a single data point, potentially injecting anomalies.

        Args:
            point: Original data point

        Returns:
            Modified data point or None (for missing)
        """
        # Check for burst missing
        if self._check_burst_missing():
            return None

        # Random missing
        if self.config.p_missing > 0 and self.rng.random() < self.config.p_missing:
            return None

        # Random outlier
        if self.config.p_outlier > 0 and self.rng.random() < self.config.p_outlier:
            return self._inject_outlier(point)

        return point

    def _check_burst_missing(self) -> bool:
        """Check if we're in a burst missing period."""
        if self._burst_active:
            self._burst_counter -= 1
            if self._burst_counter <= 0:
                self._burst_active = False
            return True

        self._points_since_last_burst += 1

        if self._points_since_last_burst >= self._points_per_day:
            if self.config.burst_missing_prob_per_day > 0 and self.rng.random() < self.config.burst_missing_prob_per_day:
                duration = self.rng.integers(
                    self.config.burst_duration_range[0],
                    self.config.burst_duration_range[1] + 1
                )
                self._burst_active = True
                self._burst_counter = int(duration)
                self._points_since_last_burst = 0
                return True
            self._points_since_last_burst = 0

        return False

    def _inject_outlier(self, point: DataPoint) -> DataPoint:
        """Inject an outlier by perturbing the value."""
        from dataclasses import replace

        if isinstance(point.value, (int, float)):
            magnitude = abs(point.value) if point.value != 0 else 1.0
            noise = self.rng.normal(0, magnitude * 3.0)
            new_value = point.value + noise
            return replace(point, value=new_value, quality=Quality.OUTLIER)

        return replace(point, quality=Quality.OUTLIER)
