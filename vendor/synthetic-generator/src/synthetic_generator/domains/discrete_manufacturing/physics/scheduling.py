"""Scheduling for discrete manufacturing.

Models shift calendar with breaks.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from typing import Optional

import numpy as np

LOG = logging.getLogger("synthetic_generator.domains.discrete_manufacturing.scheduling")


@dataclass
class ProductionOrder:
    """Production order data."""
    order_id: str
    product_id: str
    machine_id: str
    target_quantity: int
    produced_quantity: int = 0
    status: str = "PENDING"
    start_time: Optional[datetime] = None


@dataclass
class Shift:
    """Shift definition."""
    name: str
    start: time
    end: time
    days: list[str]


@dataclass
class Break:
    """Break definition."""
    name: str
    start: time
    end: time


class ShiftCalendar:
    """Shift calendar with configurable schedule."""

    WEEKDAY_MAP = {"MO": 0, "TU": 1, "WE": 2, "TH": 3, "FR": 4, "SA": 5, "SU": 6}

    def __init__(self, calendar_cfg: dict, rng: np.random.Generator):
        """Initialize shift calendar."""
        self.rng = rng
        self.shifts: list[Shift] = []
        self.breaks: list[Break] = []
        self.weekend_mode = calendar_cfg.get("weekend_mode", "reduced")
        self.weekend_prob = calendar_cfg.get("weekend_probability_run", 0.10)
        
        for shift_cfg in calendar_cfg.get("shifts", []):
            start_parts = shift_cfg["start"].split(":")
            end_parts = shift_cfg["end"].split(":")
            self.shifts.append(Shift(
                name=shift_cfg["name"],
                start=time(int(start_parts[0]), int(start_parts[1])),
                end=time(int(end_parts[0]), int(end_parts[1])),
                days=shift_cfg.get("days", ["MO", "TU", "WE", "TH", "FR"]),
            ))
        
        for break_cfg in calendar_cfg.get("breaks", []):
            start_parts = break_cfg["start"].split(":")
            end_parts = break_cfg["end"].split(":")
            self.breaks.append(Break(
                name=break_cfg["name"],
                start=time(int(start_parts[0]), int(start_parts[1])),
                end=time(int(end_parts[0]), int(end_parts[1])),
            ))

    def is_shift_active(self, dt: datetime) -> bool:
        """Check if a shift is active at given time."""
        weekday = dt.weekday()
        current_time = dt.time()
        
        for shift in self.shifts:
            shift_weekdays = [self.WEEKDAY_MAP.get(d, -1) for d in shift.days]
            if weekday not in shift_weekdays:
                continue
            
            if shift.start <= shift.end:
                if shift.start <= current_time < shift.end:
                    return True
            else:
                if current_time >= shift.start or current_time < shift.end:
                    return True
        
        if weekday >= 5:
            if self.weekend_mode == "reduced":
                return self.rng.random() < self.weekend_prob
            elif self.weekend_mode == "off":
                return False
        
        return False

    def is_break_active(self, dt: datetime) -> bool:
        """Check if a break is active at given time."""
        current_time = dt.time()
        for brk in self.breaks:
            if brk.start <= current_time < brk.end:
                return True
        return False


class Scheduler:
    """Production scheduler for manufacturing plant."""

    def __init__(self, calendar: ShiftCalendar, product_catalog: dict, scheduling_cfg: dict, rng: np.random.Generator):
        """Initialize scheduler."""
        self.calendar = calendar
        self.product_catalog = product_catalog
        self.rng = rng
        
        self.order_duration_hours_mean = scheduling_cfg.get("order_duration_hours_mean", 4)
        self.order_duration_hours_std = scheduling_cfg.get("order_duration_hours_std", 2)
        self.setup_probability = scheduling_cfg.get("setup_probability_on_order_change", 0.7)
        
        self.orders: dict[str, ProductionOrder] = {}
        self._order_counter = 0

    def is_shift_active(self, dt: datetime) -> bool:
        return self.calendar.is_shift_active(dt)

    def is_break_active(self, dt: datetime) -> bool:
        return self.calendar.is_break_active(dt)

    def is_operator_present(self, dt: datetime, machine_id: str) -> bool:
        """Check if operator is present."""
        shift_active = self.calendar.is_shift_active(dt)
        break_active = self.calendar.is_break_active(dt)
        
        if not shift_active:
            return self.rng.random() < 0.05
        if break_active:
            return self.rng.random() < 0.15
        return True

    def get_or_create_order(
        self, machine_id: str, dt: datetime, current_order: Optional[ProductionOrder]
    ) -> Optional[ProductionOrder]:
        """Get existing order or create new one."""
        if not self.calendar.is_shift_active(dt):
            return None
        
        if current_order and current_order.status == "ACTIVE":
            if current_order.start_time:
                elapsed = (dt - current_order.start_time).total_seconds() / 3600.0
                expected_duration = max(
                    self.order_duration_hours_mean + self.rng.normal(0, self.order_duration_hours_std), 1.0
                )
                if elapsed < expected_duration:
                    return current_order
                else:
                    current_order.status = "COMPLETE"
        
        self._order_counter += 1
        product_ids = list(self.product_catalog.keys())
        product_id = self.rng.choice(product_ids) if product_ids else "PRD_A"
        
        order = ProductionOrder(
            order_id=f"ORD_{dt.strftime('%Y%m%d')}_{self._order_counter:04d}",
            product_id=product_id,
            machine_id=machine_id,
            target_quantity=int(self.rng.uniform(50, 500)),
            status="ACTIVE",
            start_time=dt,
        )
        
        self.orders[machine_id] = order
        LOG.debug("Created order %s for machine %s", order.order_id, machine_id)
        return order

    def needs_setup(self, machine_id: str, new_order: ProductionOrder, current_product_id: str) -> bool:
        """Check if setup is needed for new order."""
        if not current_product_id:
            return True
        if new_order.product_id != current_product_id:
            return self.rng.random() < self.setup_probability
        return False

    def update_order_quantity(self, machine_id: str, produced: int):
        """Update order produced quantity."""
        order = self.orders.get(machine_id)
        if order:
            order.produced_quantity = produced
