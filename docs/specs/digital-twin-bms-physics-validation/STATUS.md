# STATUS — digital-twin-bms-physics-validation spec set

> Spec set hermano de `docs/specs/synthetic-bms/`. Define el framework de validación de plausibilidad física del generador BMS.

## Estado v1 — Specs entregadas

**Fecha**: 2026-05-09  
**Autor**: Claude Code (sesión Jaime Sendra)  
**Decisiones clave usuario**:
- Ejecución: una sola pasada los 13 ficheros + STATUS (decidido).
- Calibración: plausibilidad ahora con literatura (ASHRAE 62.1, EN 16798, AEMET) + comportamiento observable; ground-truth marcado como gap por regla (decidido).
- Ubicación: spec set hermano (no nested) de `synthetic-bms/` (decidido).

## Ficheros entregados

| # | Fichero | Líneas aprox | Estado |
|---|---------|-------------|--------|
| 1 | `00-research.md` | ~182 | ✓ entregado |
| 2 | `00-generator-map.md` | ~266 | ✓ entregado |
| 3 | `00-open-questions.md` | ~440 | ✓ entregado v2 (23 lagunas L-PV-NN tras revisión PPTX) |
| 4 | `01-observed-physical-model.md` | ~643 | ✓ entregado (17 modelos) |
| 5 | `02-physics-questions.md` | ~616 | ✓ entregado (40 preguntas PQ-NN) |
| 6 | `03-physical-cases.md` | ~744 | ✓ entregado (30 casos) |
| 7 | `04-physical-plausibility-rules.md` | ~839 | ✓ entregado (53 reglas R-NN) |
| 8 | `05-controlled-simulation-validation.md` | ~508 | ✓ entregado (19 experimentos) |
| 9 | `06-validation-datasets.md` | ~335 | ✓ entregado (10 datasets D-PV-NN) |
| 10 | `07-validator-design.md` | ~449 | ✓ entregado (diseño bms_physics_validator) |
| 11 | `08-physical-realism-score.md` | ~263 | ✓ entregado (10 dimensiones) |
| 12 | `09-physical-observability.md` | ~449 | ✓ entregado (Prometheus + Grafana + Influx + Loki) |
| 13 | `10-implementation-readiness.md` | ~397 | ✓ entregado (15 tasks T-PV-NN) |
| 14 | `11-production-signal-mapping.md` | ~380 | ✓ entregado v1.1 (mapeo vendor↔producción tras PPTX) |
| 15 | `STATUS.md` | (este fichero) | ✓ entregado |

**Total**: ~6,500 líneas de spec, 15 ficheros.

## Métricas del trabajo

| Métrica | Valor |
|---------|-------|
| Modelos físicos documentados con `file:line` | 17 (todos los del vendor + sus dependencias) |
| Lagunas identificadas (`L-PV-NN`) | 17 (5 críticas: L-PV-01, L-PV-02, L-PV-03, L-PV-04, L-PV-06) |
| Preguntas físicas (`PQ-NN`) | 40 |
| Casos físicos por familia (`C-*-NN`) | 30 |
| Reglas de plausibilidad (`R-*-NN`) | 53 (19 error, 22 warning, 12 info) |
| Reglas implementables hoy con confidence ≥ medium | 45 / 53 |
| Reglas bloqueadas por L-PV-02 | 5 (R-FAULT-01..05) |
| Experimentos controlados (`Exp-*-N`) | 19 (3 bloqueados) |
| Datasets de validación (`D-PV-NN`) | 10 (1 bloqueado) |
| Métricas Prometheus propuestas (`captia_physics_*`) | 8 base + 3 derivadas |
| Alertas Prometheus propuestas | 5 |
| Paneles Grafana propuestos | 12 |
| Flux tasks propuestas | 5 |
| Tareas implementación priorizadas (`T-PV-NN`) | 15 (10 prioridad alta, 5 futuras) |

## Score interno preliminar (estimado contra código actual)

**0.94** — banda "plausible con caveats" (0.85-0.95).

Caveats principales:
- D7 (averías) unscored hasta resolver L-PV-02 (peso 0.10 redistribuido).
- D2 (HVAC) en 0.90 por L-PV-07 (R-HVAC-EN-03 en low confidence).
- D6 (humedad) en 1.00 de las medium-high (R-RH-02 omitida por L-PV-09).
- D10 (CAPTIA) en 0.80 por R-INF-03 catalog incompleto (relays sin alimentar).

## Cobertura por código existente

Todas las referencias `file:line` en las specs son verificables con `Read` o `Grep` sobre el repo actual. Verificación cruzada:

- `vendor/synthetic-generator/src/synthetic_generator/domains/bms_classrooms/physics/{indoor,actuators,occupancy,environment,energy}.py` ✓
- `vendor/synthetic-generator/src/synthetic_generator/core/{anomalies,validator,control_utils,config,runner}.py` ✓
- `vendor/synthetic-generator/config/domains/bms_classrooms/{domain,variables}.yaml` ✓
- `extensions/bms_calibration/src/bms_calibration/{faults,physics_overrides,school_calendar}.py` ✓
- `modules/bms-data-generator/src/bms_data_generator/services/{runner_service,calibration_loader,dump_service}.py` ✓
- `config/domains/bms_classrooms/{domain,faults,variables}.yaml` ✓
- `docs/specs/synthetic-bms/{02-domain-spec,09-decision-log,00-open-questions}.md` ✓

## Hallazgos críticos (resumen ejecutivo)

### Hallazgos del análisis del código (v1)

1. **L-PV-01 — Catálogo divergente** (BLOCKER tras PPTX): vendor `variables.yaml` produce nombres (`temperature`, `power`, `humidity`...) que **no coinciden con producción real** (`temperature_01`, `power_01`, `relative-humidity`...) ni con `02-domain-spec.md`. Ver `11-production-signal-mapping.md`.
2. **L-PV-02 — Faults inertes**: `FaultInjector` genera eventos pero **no se materializan** en `state_events`. Caso C ML training sin etiquetas reales.
3. **L-PV-03 — Parámetros físicos ignorados**: `domain.yaml` define claves (`co2.per_person_ppm=18.5`) que **no se leen** por `physics/indoor.py` (que usa `gen_ppm_per_min_per_person=7.5` hardcoded).
4. **L-PV-04 — `calibration_loader` inerte**: definido pero **no invocado** desde `runner_service`.
5. **L-PV-05 — `ContractValidator` no enforced**: existe en vendor pero no se instancia en BMS path.
6. **L-PV-06 — Calendario duplicado**: `domain.yaml` y `ValenciaSchoolCalendar` son fuentes paralelas; el path activo usa el del vendor (incompleto), no el de extensions.
7. **L-PV-07 a L-PV-17**: gaps de modelado (anti short-cycle, cooling explícito, dehumidification, perturbations no aplicadas, anomalías limitadas, métricas validación no expuestas).

### Hallazgos adicionales tras revisión PPTX (v1.1)

8. **L-PV-18 — Bucket `telemetry_events` faltante**: producción tiene 7º bucket operativo (measurement `captia_cmd_event` para auditoría comandos / sniper errors). Ni el `init_buckets_tasks.sh` ni el Telegraf local lo soportan.
9. **L-PV-19 — Measurement state_events divergente**: producción usa `captia_point` (mismo que telemetry); nuestro Telegraf hace `name_override = "captia_point_state"`. Rompe portabilidad de queries.
10. **L-PV-20 — Streams cmd/ack/event no implementados**: producción soporta 5 streams MQTT; sintético solo `telemetry`.
11. **L-PV-21 — `captia_metadata` bucket vacío**: bucket existe pero no hay `metadata-bootstrap`. PPTX dice explícito que sin esto las Flux tasks tier-1 "terminan en success sin escribir nada" → **rollups no funcionan**.
12. **L-PV-22 — Routing on-change incompleto**: nuestro Telegraf usa solo suffix glob; producción combina glob + `metric_kind` desde catálogo.
13. **L-PV-23 — `OUTDOOR` asset separado**: producción probablemente emite meteo desde asset distinto, no per-aula.

Plan de remediación priorizado en `10-implementation-readiness.md`. Tareas T-PV-21..23 (variables alignment, telemetry_events bucket, metadata bootstrap) tras los PPTX se elevan a prioridad ALTA.

## Verificación (criterios `04-*` Verification del plan)

- ✓ **Trazabilidad code→spec**: cada modelo/ecuación/constante tiene `file:line` verificable.
- ✓ **No invención**: cada threshold se justifica con literatura citada (ASHRAE 62.1, EN 16798, EN ISO 13790, AEMET) o con código observado, o se marca `confidence: low — requiere ground-truth (L-01)`.
- ✓ **Coherencia con specs existentes**: ningún statement contradice `synthetic-bms/02-domain-spec.md` ni los ADRs en `09-decision-log.md`. Decisiones nuevas se proponen como ADR candidates en `10-implementation-readiness.md` (no se aplican aquí).
- ✓ **Diferenciación física vs dato**: las menciones a "fault" usan los 4 tipos de `extensions/bms_calibration/.../faults.py` (sensor_drift, valve_stuck, fan_failure, refrigerant_low). Las menciones a "anomalía" usan los 3 tipos del `AnomalyEngine` (missing, outlier, burst).
- ✓ **Smoke check**: `Glob "docs/specs/digital-twin-bms-physics-validation/*.md"` debe dar 14 ficheros.
- ✓ **STATUS actualizado** con métricas reales del trabajo entregado.

## Pendientes post-v1

| Pendiente | Bloqueado por | Tracking |
|-----------|---------------|----------|
| Implementación del validador (`bms_physics_validator`) | Esfuerzo dev | T-PV-01 |
| Wire `FaultEventSink` (cierra L-PV-02) | Esfuerzo dev | T-PV-08 |
| Calendario unificado (cierra L-PV-06) | Esfuerzo dev | T-PV-09 |
| Calibración real con datos IES Simarro | L-01 (CAPTIA Tech) | Hooks listos en physics_overrides.py |
| Score externo (RMSE/MAPE vs ground-truth) | L-01 | Diseño en `08-*` listo, esperar datos |
| Modelo cooling explícito + dehumidification | Esfuerzo dev v2 | T-PV-11, T-PV-12 |
| Anti short-cycle HVAC | Esfuerzo dev | T-PV-13 |
| Perturbations engine | Esfuerzo dev | T-PV-14 |
| Anomalías adicionales (stuck, drift, offset) | Esfuerzo dev | T-PV-15 |

## Estado de implementación (sprint 1, 2026-05-09)

Tareas T-PV-NN completadas tras revisión PPTX y consistencia de data:

| Task | Cierra | Cambios | Tests |
|------|--------|---------|-------|
| **T-PV-07** | L-PV-04 | `runner_service._build_runner` invoca `calibration_loader.load_faults_config` y `load_physics_overrides` | smoke + 33 unit/integ |
| **T-PV-09** | L-PV-06 | `config/domains/bms_classrooms/domain.yaml`: holidays expandidos a 50 fechas (Valencia 2025-26) | yaml validate |
| **T-PV-18** | L-PV-18 | bucket `telemetry_events` (90d) + 2º mqtt_consumer Telegraf + output #3 | TOML validate |
| **T-PV-21** | L-PV-01 | `extensions/bms_signal_alias/` paquete + AliasSinkAdapter + wire en runner & dump (BMS_PRODUCTION_ALIAS_ENABLED=true) + override `config/domains/bms_classrooms/variables.yaml` con `production_name` por entry | 11 unit + 2 integ |
| **T-PV-22** | L-PV-22 | extender Telegraf clone tagpass con `ac_control`, `aire_state` | TOML validate |
| **T-PV-23** | L-PV-21 | `populate_metadata` parser awk robusto: lee `range:[a,b]` + `production_name`, escribe measurement `captia_point_meta` (no legacy `captia_metadata`), añade tag `asset_type`, deriva `storage_mode` desde `metric_kind`, idempotente con delete previo | manual smoke parser |
| **T-PV-08** + **T-PV-30** | L-PV-02 | `extensions/bms_calibration/.../fault_event_sink.py` con `FaultEventEmitter` + wire post-run hook en `runner_service` cuando `BMS_FAULTS_ENABLED=true`. Cada FaultEvent → 2 DataPoints (start severity, end 0.0) con `variable=fault.<tipo>` que matchea Telegraf tagpass `fault.*` → state_events | 5 new tests + 2 integ |
| L-PV-19 (parche) | (parcial) | `downsample_state_1m.flux` filtra `captia_point_state` (workaround hasta resolver Telegraf rename) | n/a |

**Testing total post-sprint**:
- 11 bms_signal_alias (NEW)
- 18 bms_calibration (13 + 5 nuevos FaultEventEmitter)
- 35 bms-data-generator (33 + 2 nuevos 3-tuple factory)
- 129 vendor synthetic-generator
- **Total: 193 PASS** (sin regresiones).

**Lint**: `uv run ruff check .` → All checks passed.

## Pendientes residuales

| Task | Bloqueado por | Tracking |
|------|---------------|----------|
| **T-PV-01** — `bms_physics_validator` paquete completo | Esfuerzo dev (~2-3 sem) | `07-validator-design.md`, `04-physical-plausibility-rules.md` |
| **T-PV-19** completo — Telegraf rename `captia_point_state → captia_point` con tags routing | Esfuerzo Telegraf (~0.5-1 día), riesgo regresión | Workaround temporal aplicado (filter en Flux task) |
| **T-PV-03** — métricas Prometheus `captia_physics_*` | Esfuerzo dev (~1 día) | `09-physical-observability.md` |
| **T-PV-04..06** — InfluxDB Flux tasks de validación + dashboard `bms_physics_validation.json` + alertas | Después de T-PV-01 | `09-physical-observability.md` |
| **Calibración real** | L-01 (CAPTIA Tech) | Hooks listos en `physics_overrides.py` |
| **Score externo** (RMSE/MAPE vs ground-truth) | L-01 | Diseño en `08-*` listo |

## Próximos pasos sugeridos

1. **Smoke E2E** post-implementación: levantar stack (`make up`), verificar:
   - `/healthz`, `/readyz`, `/metrics` OK
   - Bucket `telemetry_events` creado en InfluxDB
   - Bucket `captia_metadata` poblado con 21 entries de `captia_point_meta`
   - Caso A live: MQTT publica con nombres producción (`temperature_01`, `power_01`...)
   - Caso C con `BMS_FAULTS_ENABLED=true`: state_events recibe `fault.<tipo>` series
2. **Implementar `bms_physics_validator`** (T-PV-01) — el grueso restante del spec set.
3. **Cerrar L-PV-19** completo con processor.rename Telegraf.
4. **Quando llegue L-01**: añadir spec `12-calibrated-validation.md` y enable score externo.

## Cómo navegar el spec set

```text
00-research.md                    ← punto de entrada: qué se inspeccionó y qué se halló
00-generator-map.md               ← mapa estructural visual (Mermaid)
00-open-questions.md              ← 17 lagunas L-PV-NN, severity y propuestas
01-observed-physical-model.md     ← qué hace REALMENTE cada modelo del código
02-physics-questions.md           ← 40 preguntas falseables que el generador debe superar
03-physical-cases.md              ← 30 casos físicos agrupados por 8 familias
04-physical-plausibility-rules.md ← 53 reglas concretas con thresholds y confidence
05-controlled-simulation-validation.md ← 19 experimentos (control vs treatment)
06-validation-datasets.md         ← 10 datasets de entrada para el validador
07-validator-design.md            ← diseño conceptual bms_physics_validator (NO código)
08-physical-realism-score.md      ← score multidimensional 10D, interno + externo
09-physical-observability.md      ← Prometheus + Grafana + Influx + Loki + alertas
10-implementation-readiness.md    ← qué implementar ya, en qué orden, con qué tasks
STATUS.md                         ← este fichero
```

## Convenciones

- **IDs**: `PQ-NN` (preguntas), `C-<FAMILIA>-NN` (casos), `R-<FAMILIA>-NN` (reglas), `Exp-<FAMILIA>-N` (experimentos), `D-PV-NN` (datasets), `L-PV-NN` (lagunas), `T-PV-NN` (tasks).
- **Severity**: `error` > `warning` > `info`.
- **Confidence**: `high` (literatura + observable) > `medium` > `low` (gap del modelo, diagnóstico).
- **Idioma**: español para docs, English para identificadores en bloques de código embebidos (Regla 005).
- **Schema CAPTIA**: inviolable (Regla 002). Métricas nuevas usan prefijo `captia_physics_*`.
- **Vendor**: read-only (Regla 003). Wiring vía `extensions/` o `modules/`.
