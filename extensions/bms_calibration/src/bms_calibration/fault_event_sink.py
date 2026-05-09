"""FaultEventEmitter — materializa FaultEvent → DataPoint(captia_point).

Cierra L-PV-02 cableando los eventos de avería generados por
:class:`bms_calibration.faults.FaultInjector` con el pipeline canónico
``captia_point`` → Telegraf clone+dedup (variable matchea ``fault.*``) →
bucket ``state_events`` (medición ``captia_point_state`` localmente).

Cada FaultEvent emite **2 DataPoints** al sink:
    - en ``event.start``: ``variable=fault.<tipo>``, ``value=event.severity``
      (rango [0.3, 1.0] del FaultInjector) — señal de inicio de avería.
    - en ``event.end``: ``variable=fault.<tipo>``, ``value=0.0`` — señal
      de fin de avería.

Esta convención permite a queries Flux:
    - Detectar episodios: ``filter(value > 0)``.
    - Calcular MTTF: diferencia entre ``last(value=0)`` y ``first(value > 0)``.
    - Severidad: ``last(value > 0)`` durante el evento.

Cross-ref:
    docs/specs/digital-twin-bms-physics-validation/03-physical-cases.md C-FA-01..04
    docs/specs/digital-twin-bms-physics-validation/04-physical-plausibility-rules.md R-FAULT-01..05
    docs/specs/synthetic-bms/02-domain-spec.md líneas 144-152 (etiquetado faults).
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from typing import Any

from .faults import FaultEvent

LOG = logging.getLogger("bms_calibration.fault_event_sink")


class FaultEventEmitter:
    """Translates FaultEvent → DataPoint(captia_point) and emits to sink.

    Args:
        sink: instancia que implementa ``SinkAdapterPort`` (open/emit/close).
        domain_id: e.g., ``"bms_classrooms"``.
        site_id: e.g., ``"ies_simarro"``.
    """

    def __init__(self, sink: Any, domain_id: str, site_id: str):
        self.sink = sink
        self.domain_id = domain_id
        self.site_id = site_id
        self._emitted_count = 0

    @property
    def emitted_count(self) -> int:
        return self._emitted_count

    def emit_events(self, events: Iterable[FaultEvent]) -> int:
        """Emit start+end DataPoints for each event. Returns total points emitted."""
        # Lazy import vendor models to keep tests light.
        from synthetic_generator.core.models import (  # type: ignore[import-not-found]
            DataPoint,
            DataType,
            PointType,
            Quality,
        )

        count = 0
        for event in events:
            variable = f"fault.{event.fault_type.value}"
            base_kwargs: dict[str, Any] = dict(
                domain_id=self.domain_id,
                site_id=self.site_id,
                asset_id=event.asset_id,
                variable=variable,
                unit="bool",
                data_type=DataType.FLOAT,
                point_type=PointType.SENSOR,
                quality=Quality.OK,
                origin="synthetic_fault",
            )
            self.sink.emit(
                DataPoint(
                    timestamp=event.start,
                    value=float(event.severity),
                    **base_kwargs,
                )
            )
            self.sink.emit(
                DataPoint(
                    timestamp=event.end,
                    value=0.0,
                    **base_kwargs,
                )
            )
            count += 2
        self._emitted_count += count
        LOG.info("FaultEventEmitter: emitted %d datapoints (total: %d)", count, self._emitted_count)
        return count
