# Visión general — qué es y por qué

> **Última verificación:** 2026-05-10

## Qué es

CAPTIA Synthetic Data BMS es un **microservicio generador de datos
sintéticos** para Building Management Systems (aulas educativas IES
Simarro). Reproduce el pipeline canónico CAPTIA `MQTT → Telegraf →
InfluxDB → Grafana` con un generador hexagonal vendoreado.

## Por qué existe

El proyecto del Curso de Especialización IA & Big Data necesita datos para
entrenar modelos cuando los sensores reales del IES Simarro aún no han
acumulado suficiente histórico. Una vez calibrado con la experiencia real
de CAPTIA, el generador podrá usarse:

- En este curso (mayo 2026).
- En cursos futuros.
- Para arrancar nuevos centros CENTINELA+ sin esperar meses de datos.
- Para entrenar modelos contra escenarios de fallo poco frecuentes.

## Qué hace

1. Genera telemetría continua y on-change con el schema canónico CAPTIA
   (`captia_point` + 5 tags + field `value`).
2. Publica a Mosquitto con topics canónicos.
3. Soporta backfill 1–12 meses con `seed=42` reproducible.
4. Inyecta fallos HVAC etiquetados (Caso C).
5. Expone API HTTP para control y export de datasets.
6. Dashboards Grafana provisionados.

## Cómo se usa

- **Para entrenar un modelo de forecast** (Caso B): backfill 12 meses,
  `influx restore` del dump.
- **Para detectar anomalías HVAC** (Caso C): backfill con
  `BMS_FAULTS_ENABLED=true`.
- **Para clase**: `make demo` levanta todo en ~90 s.

## Qué hay en este sitio

- [Empezar](index.md) — Quickstart y setup.
- [Arquitectura](../architecture/index.md) — diagrama de servicios y reglas.
- [Casos de uso](../use-cases/index.md) — 10 casos + extra.
- [Notebooks](../notebooks/index.md) — 45 notebooks didácticos.
- [Contratos](../contracts/influx-schema.md) — schema, topics, variables.
- [Validación](../validation/e2e.md) — tests, calidad de datos, realismo.
- [Operación](../operations/troubleshooting.md) — troubleshooting, env.
- [Auditoría](../audit/index.md) — fases, hallazgos, plan de acción.

## Estado actual

- Suite tests: **211/211 PASS**.
- Score realismo físico: **0.94**.
- Notebooks: **45** (todos abren, todos siguen las 18 secciones).
- Auditoría extrema: **11/11 fases cerradas**.
