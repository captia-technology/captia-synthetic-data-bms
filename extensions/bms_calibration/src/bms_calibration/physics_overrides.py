"""Hooks de override para parámetros físicos BMS (post-v1).

Por defecto todos los hooks devuelven ``None`` (no override). Cuando estén
disponibles los parámetros calibrados con datos reales del IES Simarro,
sobrescribir aquí.

Defaults literatura (cuando override es ``None``):

- ``co2_rise_rate_per_person_per_min``: 4.5 ppm/persona/min (ASHRAE 62.1, EN 16798).
- ``hvac_response_time_minutes``: 8 min.
- ``temp_outdoor_indoor_coupling``: 0.15 (envolvente típica).
"""

from __future__ import annotations

from typing import Any


def co2_rise_rate_per_person_per_min() -> float | None:
    """Tasa de subida de CO2 por persona y minuto, ppm/persona/min."""
    return None


def hvac_response_time_minutes() -> float | None:
    """Tiempo de respuesta del HVAC en minutos."""
    return None


def temp_outdoor_indoor_coupling() -> float | None:
    """Coeficiente de acoplamiento térmico exterior-interior (adimensional)."""
    return None


def get_overrides() -> dict[str, Any]:
    """Devuelve solo los hooks con valor distinto de ``None``."""
    overrides: dict[str, Any] = {}
    for fn_name in (
        "co2_rise_rate_per_person_per_min",
        "hvac_response_time_minutes",
        "temp_outdoor_indoor_coupling",
    ):
        value = globals()[fn_name]()
        if value is not None:
            overrides[fn_name] = value
    return overrides
