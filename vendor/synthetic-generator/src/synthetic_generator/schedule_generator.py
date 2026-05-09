from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd


def _parse_time(t: str) -> time:
    return datetime.strptime(t, "%H:%M").time()


@dataclass(frozen=True)
class Slot:
    name: str
    start: time
    end: time
    p_occupied: float


def build_slots(cfg_schedule: Dict[str, Any]) -> List[Slot]:
    slots: list[Slot] = []
    for i, s in enumerate(cfg_schedule.get("slots", [])):
        name = s.get("name", f"slot_{i+1}")
        p_occ = float(s.get("p_occupied", s.get("p_occupancy", 0.0)))
        slots.append(Slot(
            name=name,
            start=_parse_time(s["start"]),
            end=_parse_time(s["end"]),
            p_occupied=p_occ,
        ))
    return slots


def occupancy_probability(index: pd.DatetimeIndex, school_mask: pd.Series, slots: List[Slot]) -> pd.Series:
    p = np.zeros(len(index), dtype=float)
    times = index.time
    for i, tt in enumerate(times):
        if not bool(school_mask.iat[i]):
            p[i] = 0.0
            continue
        # find slot
        assigned = 0.0
        for s in slots:
            if s.start <= tt < s.end:
                assigned = s.p_occupied
                break
        p[i] = assigned
    return pd.Series(p, index=index)
