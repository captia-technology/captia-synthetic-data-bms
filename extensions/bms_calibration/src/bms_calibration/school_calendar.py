"""Calendario lectivo Comunidad Valenciana curso 2025-2026."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class _Period:
    start: date
    end: date


class ValenciaSchoolCalendar:
    """Calendario escolar Comunidad Valenciana, curso 2025-2026.

    Devuelve si una fecha es lectiva considerando fines de semana y los
    periodos vacacionales oficiales del curso 2025-2026.
    """

    _BREAKS_2025_2026: tuple[_Period, ...] = (
        _Period(date(2025, 12, 22), date(2026, 1, 7)),
        _Period(date(2026, 3, 14), date(2026, 3, 19)),
        _Period(date(2026, 4, 4), date(2026, 4, 12)),
        _Period(date(2026, 6, 20), date(2026, 9, 7)),
    )

    def __init__(self, year_start: int = 2025) -> None:
        if year_start != 2025:
            raise NotImplementedError("Only the 2025-2026 school year is supported in v1")
        self._year_start = year_start

    def is_lectivo(self, day: date) -> bool:
        if day.weekday() >= 5:
            return False
        return not any(period.start <= day <= period.end for period in self._BREAKS_2025_2026)

    def is_vacation(self, day: date) -> bool:
        return any(period.start <= day <= period.end for period in self._BREAKS_2025_2026)
