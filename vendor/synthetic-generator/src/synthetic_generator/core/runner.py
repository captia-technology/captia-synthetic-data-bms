"""ScenarioRunner — orchestrates the full generation lifecycle.

Ref: docs/specs/core-architecture.md Section 2.1
"""

from __future__ import annotations

import logging
import os
import signal
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from .clock import ClockPort, SystemClock
from .config import ScenarioConfig
from .models import DataPoint
from .time_index import build_time_index
from .validator import ContractValidator
from .anomalies import AnomalyEngine, AnomalyConfig as CoreAnomalyConfig
from ..ports.domain import DomainAdapterPort
from ..ports.sink import SinkAdapterPort
from ..health import get_metrics, get_health

LOG = logging.getLogger(__name__)


@dataclass
class RunResult:
    points_emitted: int = 0
    points_skipped: int = 0
    validation_errors: int = 0
    elapsed_seconds: float = 0.0
    phase: str = ""


class ScenarioRunner:
    """Orchestrates backfill and live phases for a scenario."""

    def __init__(
        self,
        config: ScenarioConfig,
        domain_adapter: DomainAdapterPort,
        sink: SinkAdapterPort,
        clock: ClockPort | None = None,
        validator: ContractValidator | None = None,
    ):
        self.config = config
        self.domain = domain_adapter
        self.sink = sink
        self.clock = clock or SystemClock()
        self.validator = validator
        self._running = True
        self._metrics = get_metrics()
        self._health = get_health()

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        LOG.info("Received signal %d, stopping...", signum)
        self._running = False

    def run(self) -> list[RunResult]:
        """Execute all configured phases."""
        results = []
        self.sink.open()
        try:
            if self.config.phases.backfill.enabled:
                results.append(self.run_backfill())
            if self.config.phases.live.enabled:
                results.append(self.run_live())
        finally:
            self.sink.flush()
            self.sink.close()
        return results

    def run_backfill(self) -> RunResult:
        """Execute backfill phase: generate historical data."""
        t0 = time.monotonic()
        result = RunResult(phase="backfill")

        sim = self.config.simulation
        time_index = build_time_index(sim.start, sim.end, sim.freq, sim.timezone)
        LOG.info("Backfill: %d timestamps (%s to %s)", len(time_index), time_index[0], time_index[-1])

        rng = np.random.default_rng(sim.seed)

        # Load domain config
        domain_cfg = self._load_domain_config()

        # Build inventory and context
        project_dict = self.config.project.model_dump()
        inventory = self.domain.build_inventory(project_dict, domain_cfg)
        ctx = self.domain.build_context(time_index, project_dict, domain_cfg, rng)

        if self.validator is None:
            self.validator = ContractValidator(inventory=inventory)

        # Simulate
        LOG.info("Generating data for %d assets...", len(inventory.assets))
        points_iter = self.domain.simulate(time_index, inventory, ctx, rng)

        # Apply anomalies if configured
        anom = self.config.anomalies
        if anom.p_missing > 0 or anom.p_outlier > 0:
            engine = AnomalyEngine(
                CoreAnomalyConfig(
                    p_missing=anom.p_missing,
                    p_outlier=anom.p_outlier,
                    burst_missing_prob_per_day=anom.burst_missing_prob_per_day,
                    burst_duration_range=anom.burst_duration_range,
                ),
                rng,
            )
            points_iter = engine.apply(points_iter)

        # Emit
        batch: list[DataPoint] = []
        for point in points_iter:
            vr = self.validator.validate(point)
            if not vr.valid:
                result.validation_errors += 1
                continue
            batch.append(point)
            if len(batch) >= 1000:
                result.points_emitted += self.sink.emit_batch(batch)
                batch.clear()

        if batch:
            result.points_emitted += self.sink.emit_batch(batch)

        self.sink.flush()
        result.elapsed_seconds = time.monotonic() - t0
        LOG.info(
            "Backfill complete: %d points in %.1fs (%.0f pts/s)",
            result.points_emitted,
            result.elapsed_seconds,
            result.points_emitted / max(result.elapsed_seconds, 0.001),
        )
        return result

    def run_live(self) -> RunResult:
        """Execute live phase: stream data to sinks in real-time.

        1. Generate dataset from ``datetime.now()`` to
           ``now + lookahead_hours`` so timestamps ARE current.
        2. Group by timestamp; iterate one batch per interval.
        3. Sleep ``GENERATOR_INTERVAL_SECONDS`` between batches.
        4. When the dataset is exhausted, regenerate from a new
           ``datetime.now()``.
        """
        from collections import defaultdict
        from datetime import datetime, timedelta

        t0 = time.monotonic()
        result = RunResult(phase="live")
        sim = self.config.simulation
        live = self.config.phases.live

        interval_seconds = float(
            os.environ.get(
                "GENERATOR_INTERVAL_SECONDS",
                pd.Timedelta(sim.freq).total_seconds(),
            )
        )

        LOG.info(
            "Live phase started: interval=%.1fs, lookahead=%dh, regenerate=%s",
            interval_seconds,
            live.lookahead_hours,
            live.regenerate_on_exhaustion,
        )

        rng = np.random.default_rng(sim.seed)
        domain_cfg = self._load_domain_config()
        project_dict = self.config.project.model_dump()

        # Update health status - ready to run
        self._health.loop_running = True
        self._health.healthy = True

        LOG.info("Starting publisher loop (interval=%.1fs)", interval_seconds)

        # Main loop - publish by timestamp batch (same as mqtt_publisher_v2.run)
        try:
            while self._running:
                # Generate from NOW (same as mqtt_publisher_v2._generate_dataset)
                now = datetime.now()
                end = now + timedelta(hours=live.lookahead_hours)
                time_index = pd.date_range(
                    start=now.strftime("%Y-%m-%d %H:%M:%S"),
                    end=end.strftime("%Y-%m-%d %H:%M:%S"),
                    freq=sim.freq,
                    tz=sim.timezone,
                )

                LOG.info("Live: generating %d timestamps (%s to %s)", len(time_index), time_index[0], time_index[-1])

                inventory = self.domain.build_inventory(project_dict, domain_cfg)
                ctx = self.domain.build_context(time_index, project_dict, domain_cfg, rng)
                all_points = list(self.domain.simulate(time_index, inventory, ctx, rng))

                self._metrics.points_generated_total += len(all_points)

                # Group by timestamp
                groups: dict[Any, list[DataPoint]] = defaultdict(list)
                for p in all_points:
                    groups[p.timestamp].append(p)

                timestamps = sorted(groups.keys())
                LOG.info("Live chunk ready: %d timestamps, %d points", len(timestamps), len(all_points))

                # Stream one timestamp-batch per interval
                timestamp_idx = 0
                while self._running and timestamp_idx < len(timestamps):
                    loop_start = time.time()
                    ts = timestamps[timestamp_idx]
                    batch = groups[ts]

                    batch_start = time.time()
                    for point in batch:
                        self.sink.emit(point)
                        result.points_emitted += 1
                        self._metrics.messages_published_total += 1

                    # Update metrics (same as mqtt_publisher_v2._publish_timestamp_batch)
                    batch_duration_ms = (time.time() - batch_start) * 1000
                    self._metrics.last_publish_duration_ms = batch_duration_ms
                    self._metrics.current_batch_size = len(batch)
                    self._metrics.cycles_completed_total += 1

                    LOG.debug("Published %d points for timestamp %s", len(batch), ts)

                    timestamp_idx += 1

                    # Sleep remaining interval (discount publish time)
                    elapsed = time.time() - loop_start
                    sleep_time = max(0, interval_seconds - elapsed)
                    if sleep_time > 0 and timestamp_idx < len(timestamps):
                        self.clock.sleep(sleep_time)

                if not self._running:
                    break

                if not live.regenerate_on_exhaustion:
                    break

                LOG.info("Live chunk exhausted (%d points), regenerating from now...", result.points_emitted)
                self._metrics.dataset_regenerations_total += 1

        except KeyboardInterrupt:
            LOG.info("Interrupted by user")

        finally:
            LOG.info("Publisher stopped")
            self._health.loop_running = False

        result.elapsed_seconds = time.monotonic() - t0
        return result

    def _load_domain_config(self) -> dict[str, Any]:
        """Load domain-specific config from referenced file."""
        cfg_path = self.config.domain.config_path
        if not cfg_path:
            return {}
        p = Path(cfg_path)
        if not p.is_absolute():
            # Try relative to CWD
            if not p.exists():
                LOG.warning("Domain config not found: %s", cfg_path)
                return {}
        try:
            with open(p, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            LOG.warning("Domain config file not found: %s", p)
            return {}
