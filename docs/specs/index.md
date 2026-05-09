# Especificaciones (SDD)

> **Última verificación:** 2026-05-10
> Fuente de verdad técnica: aquí se mantienen las especificaciones SDD versionadas. Cambios no triviales requieren actualizar la spec correspondiente y propagar al plan/tareas/tests.

## Suites de specs

### `synthetic-bms/`

Especificaciones del microservicio generador BMS y su infraestructura.

| Archivo | Propósito |
|---|---|
| [`STATUS.md`](synthetic-bms/STATUS.md) | Estado vivo de las fases SDD |
| [`00-research-report.md`](synthetic-bms/00-research-report.md) | Investigación documentada (10 secciones) |
| [`00-open-questions.md`](synthetic-bms/00-open-questions.md) | Lagunas L-01..L-14 (resueltas y pendientes) |
| [`00-repo-map.md`](synthetic-bms/00-repo-map.md) | Mapa repo target + repo de referencia |
| [`01-product-spec.md`](synthetic-bms/01-product-spec.md) | Goal, casos de uso, acceptance |
| [`02-domain-spec.md`](synthetic-bms/02-domain-spec.md) | BMS entities, variables, modelo de fallos |
| [`03-architecture-spec.md`](synthetic-bms/03-architecture-spec.md) | Hexagonal, vendoring, flujos |
| [`04-infra-spec.md`](synthetic-bms/04-infra-spec.md) | Compose, MQTT, InfluxDB, Redis, Grafana |
| [`05-observability-spec.md`](synthetic-bms/05-observability-spec.md) | Métricas, logs, dashboards, alertas |
| [`06-api-and-ui-spec.md`](synthetic-bms/06-api-and-ui-spec.md) | Control plane, datasets, auth |
| [`07-testing-spec.md`](synthetic-bms/07-testing-spec.md) | Pirámide, fixtures, markers |
| [`08-task-plan.md`](synthetic-bms/08-task-plan.md) | Tareas con trazabilidad RF/RNF |
| [`09-decision-log.md`](synthetic-bms/09-decision-log.md) | ADRs aceptadas |
| [`10-validation-checklist.md`](synthetic-bms/10-validation-checklist.md) | Checklist final |

### `digital-twin-bms-physics-validation/`

Especificaciones del modelo físico del digital twin BMS.

| Archivo | Propósito |
|---|---|
| [`STATUS.md`](digital-twin-bms-physics-validation/STATUS.md) | Estado vivo |
| [`00-research.md`](digital-twin-bms-physics-validation/00-research.md) | Investigación |
| [`00-generator-map.md`](digital-twin-bms-physics-validation/00-generator-map.md) | Mapeo del generador a las variables físicas |
| [`00-open-questions.md`](digital-twin-bms-physics-validation/00-open-questions.md) | Open questions L-PV-* |
| [`01-observed-physical-model.md`](digital-twin-bms-physics-validation/01-observed-physical-model.md) | Modelo físico observado |
| [`02-physics-questions.md`](digital-twin-bms-physics-validation/02-physics-questions.md) | Open questions L-PV-* |
| [`03-physical-cases.md`](digital-twin-bms-physics-validation/03-physical-cases.md) | 30 casos físicos |
| [`04-physical-plausibility-rules.md`](digital-twin-bms-physics-validation/04-physical-plausibility-rules.md) | 53 reglas R-* |
| [`05-controlled-simulation-validation.md`](digital-twin-bms-physics-validation/05-controlled-simulation-validation.md) | Validación controlada |
| [`06-validation-datasets.md`](digital-twin-bms-physics-validation/06-validation-datasets.md) | Datasets de referencia |
| [`07-validator-design.md`](digital-twin-bms-physics-validation/07-validator-design.md) | Diseño del validador |
| [`08-physical-realism-score.md`](digital-twin-bms-physics-validation/08-physical-realism-score.md) | Score y dimensiones |
| [`09-physical-observability.md`](digital-twin-bms-physics-validation/09-physical-observability.md) | Observabilidad física |
| [`10-implementation-readiness.md`](digital-twin-bms-physics-validation/10-implementation-readiness.md) | Readiness |
| [`11-production-signal-mapping.md`](digital-twin-bms-physics-validation/11-production-signal-mapping.md) | Mapeo a señales reales |

## Política

- Las specs son la **fuente de verdad** para alcance, contratos y comportamiento.
- Toda implementación deriva de una spec. Nuevas features sin spec → ADR de excepción + spec a posteriori.
- Las specs no se modifican en silencio: cualquier cambio require commit + nota en `STATUS.md`.
