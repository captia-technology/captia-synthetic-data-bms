# 00 — Lagunas y preguntas abiertas

> Inventario de ambigüedades detectadas durante la investigación. Cada laguna tiene una decisión asociada (resuelta) o queda como ítem pendiente con responsable.

## Resueltas durante la planificación (decisiones del usuario)

| ID | Pregunta | Resolución | Referencia |
|----|----------|-----------|------------|
| L-06 | ¿El generador es entregable o solo parámetros? | Microservicio en vivo + dump exportable. | Decisión del usuario; ADR-001 / ADR-003 |
| L-09 | ¿Resolución temporal mínima del dump? | 5 s telemetría raw + agregaciones automáticas Telegraf/InfluxDB. | ADR-007 |
| L-14 | ¿UI custom o Grafana? | Grafana provisionado; sin UI propia v1. | ADR-011 |
| L-03 | ¿Anonimización de dump real o sintético puro? | Sintético puro. | ADR-001 (alcance) |
| L-05 | ¿Etiquetas de fallo en dump? | Sí: bucket `state_events` con `variable=fault.<tipo>`. | ADR-010 |
| L-02 | ¿Tipos de fallos HVAC? | 4 tipos v1: `sensor_drift`, `valve_stuck`, `fan_failure`, `refrigerant_low`. | ADR-010 |
| L-07 | ¿Períodos sin datos (vacaciones)? | Valores base con ocupación 0; no NaN. | ADR-007 |
| L-08 | ¿Caso C suficiente sin fallos reales? | Aceptado para v1; mejora post-v1 con datos reales LBNL FDD. | ADR-010 |
| L-10 | ¿ERA5 en dump v1? | NO incluido; cada equipo descarga ERA5. | Alcance v1 |
| L-12 | ¿Plazo 12 mayo 2026? | Trazado en `08-task-plan.md`. | Plan de tareas |
| L-13 | ¿Plan B sin parámetros calibración? | Defaults literatura ASHRAE 62.1 / EN 16798. | ADR-010 / ADR-013 |

## Pendientes (impacto en v1, monitorizadas)

| ID | Pregunta | Impacto | Responsable / Acción |
|----|----------|--------|---------------------|
| L-01 | ¿Parámetros calibración real (co2_rise, hvac_response, temp_coupling)? | Alto: sin calibración, datos sintéticos pueden divergir de realidad. | Hooks en `extensions/bms_calibration/physics_overrides.py`; trabajo de calibración fuera de v1. CAPTIA Technology proporciona valores cuando estén disponibles. |

## Pendientes (post-v1)

| ID | Pregunta | Por qué fuera de v1 |
|----|----------|---------------------|
| L-04 | ¿Infra final ITI/Simarro semana 3? | Decisión organizativa; no afecta ejecutables del repo. |
| L-11 | ¿Política anonimización si dump real? | No aplica (sintético puro v1). |

## Notas operativas

- Si CAPTIA Technology proporciona parámetros calibrados, sobrescribir en `extensions/bms_calibration/physics_overrides.py` y registrar como ADR-016 en `09-decision-log.md`.
- Si en algún momento se acepta dump real (fuera de v1), abrir spec separada y documentar política anonimización (L-11).
