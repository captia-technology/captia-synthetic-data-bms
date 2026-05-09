"""Inyector de fallos HVAC para escenarios sintéticos BMS (Caso C).

Genera eventos de fallo etiquetables con frecuencia configurable. Los eventos
se materializan luego en el bucket `state_events` con `variable=fault.<tipo>`.

Tipos soportados (ADR-010):
    - sensor_drift: deriva acumulativa en sensores de temperatura.
    - valve_stuck: válvula bloqueada en último estado.
    - fan_failure: ventilador caído (potencia y rpm a 0).
    - refrigerant_low: caudal frigorífico insuficiente (T_supply ≈ T_return).
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

import numpy as np


class FaultType(str, Enum):
    SENSOR_DRIFT = "sensor_drift"
    VALVE_STUCK = "valve_stuck"
    FAN_FAILURE = "fan_failure"
    REFRIGERANT_LOW = "refrigerant_low"


@dataclass(frozen=True)
class FaultEvent:
    fault_type: FaultType
    asset_id: str
    start: datetime
    end: datetime
    severity: float


class FaultInjector:
    """Inyector determinista de fallos.

    El RNG se construye desde `seed` para garantizar reproducibilidad.
    """

    def __init__(
        self,
        rng: np.random.Generator,
        config: dict[str, dict],
        seed: int = 42,
    ) -> None:
        self._rng = np.random.default_rng(seed)
        self._config = config

    def inject(
        self,
        timestamps: list[datetime],
        asset_id: str,
    ) -> Iterator[FaultEvent]:
        if not timestamps:
            return
        days = max((timestamps[-1] - timestamps[0]).total_seconds() / 86400, 1.0)
        for ftype_name, params in self._config.items():
            ftype = FaultType(ftype_name)
            prob = float(params["probability_per_day"])
            n_events = int(self._rng.poisson(prob * days))
            for _ in range(n_events):
                start_idx = int(self._rng.integers(0, len(timestamps)))
                start = timestamps[start_idx]
                duration_min = float(params.get("duration_minutes", 30))
                end = start + timedelta(minutes=duration_min)
                severity = float(self._rng.uniform(0.3, 1.0))
                yield FaultEvent(
                    fault_type=ftype,
                    asset_id=asset_id,
                    start=start,
                    end=end,
                    severity=severity,
                )
