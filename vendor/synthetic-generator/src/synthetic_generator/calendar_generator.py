from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date, time
from typing import Iterable, List, Dict, Any, Tuple

import pandas as pd


def _parse_date(d: str) -> date:
    return datetime.strptime(d, "%Y-%m-%d").date()


def _parse_time(t: str) -> time:
    return datetime.strptime(t, "%H:%M").time()


@dataclass(frozen=True)
class CalendarSpec:
    school_days: set[int]  # 0=Mon..6=Sun
    holidays: set[date]
    vacations: list[tuple[date, date]]  # inclusive start/end
    daily_start: time
    daily_end: time


def build_calendar_spec(cfg_calendar: Dict[str, Any]) -> CalendarSpec:
    weekday_map = {"MO":0,"TU":1,"WE":2,"TH":3,"FR":4,"SA":5,"SU":6}
    school_days = {weekday_map[x] for x in cfg_calendar.get("school_days", ["MO","TU","WE","TH","FR"])}

    holidays = {_parse_date(x) for x in cfg_calendar.get("holidays", [])}

    vacations = []
    for v in cfg_calendar.get("vacations", []):
        vacations.append((_parse_date(v["start"]), _parse_date(v["end"])))

    daily_start = _parse_time(cfg_calendar.get("daily_start_time", "08:00"))
    daily_end = _parse_time(cfg_calendar.get("daily_end_time", "14:00"))
    return CalendarSpec(school_days=school_days, holidays=holidays, vacations=vacations, daily_start=daily_start, daily_end=daily_end)


def is_vacation_day(d: date, spec: CalendarSpec) -> bool:
    for s, e in spec.vacations:
        if s <= d <= e:
            return True
    return False


def is_school_day(d: date, spec: CalendarSpec) -> bool:
    if d.weekday() not in spec.school_days:
        return False
    if d in spec.holidays:
        return False
    if is_vacation_day(d, spec):
        return False
    return True


def school_mask(index: pd.DatetimeIndex, spec: CalendarSpec) -> pd.Series:
    # mask for timestamps during school days AND inside daily window
    dates = pd.Series(index.date, index=index)
    in_school_day = dates.apply(lambda d: is_school_day(d, spec))

    t = pd.Series(index.time, index=index)
    in_window = t.apply(lambda tt: spec.daily_start <= tt < spec.daily_end)
    return (in_school_day & in_window)
