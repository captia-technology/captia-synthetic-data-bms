"""Production simulation for discrete manufacturing.

Models production cycles with support for pieces_per_cycle.
"""
from __future__ import annotations

import logging
import numpy as np

from ..state import MachineState, InternalMachineState, ProductionCounters

LOG = logging.getLogger("synthetic_generator.domains.discrete_manufacturing.production")


class ProductionSimulator:
    """Simulates production cycles for machines.
    
    Key features:
    - Support for pieces_per_cycle (e.g. welding robot with 11)
    - Lognormal cycle time distribution
    - Warmup period after setup with elevated scrap
    - Quality outcomes (good/scrap/rework)
    - Monotonic counters
    """

    def __init__(self, physics_cfg: dict, product_catalog: dict, rng: np.random.Generator):
        """Initialize production simulator."""
        self.physics_cfg = physics_cfg
        self.product_catalog = product_catalog
        self.rng = rng
        
        ct_cfg = physics_cfg.get("cycle_time", {})
        self.cv_base = ct_cfg.get("cv_base", 0.10)
        self.cv_wear_gain = ct_cfg.get("cv_wear_gain", 0.04)
        
        warmup_cfg = physics_cfg.get("warmup", {})
        self.warmup_cycles = warmup_cfg.get("cycles_elevated_scrap", 5)
        self.warmup_scrap_mult = warmup_cfg.get("scrap_multiplier", 3.0)

    def step(
        self,
        machine: MachineState,
        dt_seconds: float,
        scrap_rate_modifier: float = 1.0,
        ct_modifier: float = 1.0
    ) -> int:
        """Execute one simulation step for production.
        
        Returns:
            Number of cycles completed this step (usually 0 or 1)
        """
        cycle = machine.cycle
        counters = machine.counters
        cycles_completed = 0
        
        # Only produce when machine_state is true (BOOLEAN check)
        if not machine.di_signals.machine_state:
            cycle.in_progress = False
            return 0
        
        product = self.product_catalog.get(machine.product_id, {})
        ct_factor = product.get("ideal_cycle_time_factor", 1.0)
        scrap_factor = product.get("scrap_factor", 1.0)
        
        ideal_ct = machine.config.cycle_time_ideal_s * ct_factor
        machine.ideal_cycle_time_sp = ideal_ct
        
        if not cycle.in_progress:
            cycle.in_progress = True
            cycle.elapsed_s = 0.0
            
            wear = machine.condition.tool_wear_index
            cv = self.cv_base + self.cv_wear_gain * wear
            sigma_log = np.sqrt(np.log(1 + cv**2))
            mu_log = np.log(ideal_ct * ct_modifier) - sigma_log**2 / 2
            
            cycle.target_duration_s = self.rng.lognormal(mu_log, sigma_log)
            cycle.target_duration_s = np.clip(cycle.target_duration_s, ideal_ct * 0.5, ideal_ct * 2.0)
        
        cycle.elapsed_s += dt_seconds
        
        if cycle.elapsed_s >= cycle.target_duration_s:
            cycle.in_progress = False
            cycle.last_cycle_time_s = cycle.elapsed_s
            cycles_completed = 1
            
            counters.cycle_count_total += 1
            counters.cycles_since_setup += 1
            
            pieces_per_cycle = machine.config.pieces_per_cycle
            self._process_pieces(machine, pieces_per_cycle, scrap_rate_modifier * scrap_factor)
            
            LOG.debug(
                "Machine %s: Cycle complete, CT=%.1fs, pieces=%d, total_good=%d",
                machine.machine_id, cycle.last_cycle_time_s,
                pieces_per_cycle, counters.good_count_total
            )
        
        machine.cycle = cycle
        machine.counters = counters
        machine.di_signals.cycle_in_progress = cycle.in_progress
        
        return cycles_completed

    def _process_pieces(self, machine: MachineState, pieces: int, scrap_modifier: float) -> None:
        """Process quality outcomes for pieces in completed cycle."""
        cfg = machine.config
        counters = machine.counters
        
        base_scrap = cfg.nominal_scrap_rate
        base_rework = cfg.nominal_rework_rate
        
        if counters.cycles_since_setup <= self.warmup_cycles:
            warmup_factor = self.warmup_scrap_mult * (1 - counters.cycles_since_setup / self.warmup_cycles)
            effective_scrap = base_scrap * (1 + warmup_factor) * scrap_modifier
            effective_rework = base_rework * (1 + warmup_factor * 0.5) * scrap_modifier
        else:
            effective_scrap = base_scrap * scrap_modifier
            effective_rework = base_rework * scrap_modifier
        
        good = 0
        scrap = 0
        rework = 0
        
        for _ in range(pieces):
            rand = self.rng.random()
            if rand < effective_scrap:
                scrap += 1
            elif rand < effective_scrap + effective_rework:
                rework += 1
            else:
                good += 1
        
        counters.good_count_total += good
        counters.scrap_count_total += scrap
        counters.rework_count_total += rework

    def validate_counters(self, machine: MachineState) -> bool:
        """Validate counter coherence."""
        c = machine.counters
        cfg = machine.config
        
        if any(x < 0 for x in [c.cycle_count_total, c.good_count_total, c.scrap_count_total, c.rework_count_total]):
            return False
        
        expected_total = c.cycle_count_total * cfg.pieces_per_cycle
        actual_total = c.good_count_total + c.scrap_count_total + c.rework_count_total
        
        if actual_total != expected_total:
            LOG.warning("Machine %s: Counter mismatch - expected %d pieces, got %d",
                       machine.machine_id, expected_total, actual_total)
            return False
        
        return True
