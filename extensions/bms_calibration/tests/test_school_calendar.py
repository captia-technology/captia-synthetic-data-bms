from datetime import date

import pytest

from bms_calibration.school_calendar import ValenciaSchoolCalendar


@pytest.fixture
def calendar() -> ValenciaSchoolCalendar:
    return ValenciaSchoolCalendar(year_start=2025)


@pytest.mark.unit
def test_school_day_is_lectivo(calendar: ValenciaSchoolCalendar) -> None:
    # 15-sep-2025 es lunes en periodo lectivo
    assert calendar.is_lectivo(date(2025, 9, 15)) is True


@pytest.mark.unit
def test_weekend_is_not_lectivo(calendar: ValenciaSchoolCalendar) -> None:
    # 13/14-sep-2025 son sábado/domingo
    assert calendar.is_lectivo(date(2025, 9, 13)) is False
    assert calendar.is_lectivo(date(2025, 9, 14)) is False


@pytest.mark.unit
def test_christmas_break_not_lectivo(calendar: ValenciaSchoolCalendar) -> None:
    assert calendar.is_lectivo(date(2025, 12, 24)) is False
    assert calendar.is_lectivo(date(2026, 1, 7)) is False


@pytest.mark.unit
def test_summer_break_not_lectivo(calendar: ValenciaSchoolCalendar) -> None:
    assert calendar.is_lectivo(date(2026, 7, 15)) is False


@pytest.mark.unit
def test_unsupported_year_raises() -> None:
    with pytest.raises(NotImplementedError):
        ValenciaSchoolCalendar(year_start=2030)


@pytest.mark.unit
def test_is_vacation_inverse_of_lectivo_for_weekday(calendar: ValenciaSchoolCalendar) -> None:
    # Día lectivo NO es vacación
    assert calendar.is_vacation(date(2025, 9, 15)) is False
    # Día en navidad SÍ es vacación
    assert calendar.is_vacation(date(2025, 12, 26)) is True
