# bms_calibration

Extensiones BMS para `synthetic-generator`:

- `school_calendar.ValenciaSchoolCalendar` — calendario lectivo Valencia 2025-2026.
- `faults.FaultInjector` + `FaultType` — inyector de 4 tipos de fallos HVAC.
- `physics_overrides` — hooks para parámetros de calibración real (defaults `None`).

## Reglas

- No importa `synthetic_generator.sinks.*` ni `synthetic_generator.domains.bms_classrooms.physics.*`.
- Solo importa `synthetic_generator.ports.*` y `synthetic_generator.core.models`.

Ver `docs/specs/synthetic-bms/02-domain-spec.md` y `09-decision-log.md` (ADR-010).
