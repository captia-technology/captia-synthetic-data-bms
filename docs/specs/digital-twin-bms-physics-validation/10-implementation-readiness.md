# 10 — Implementation readiness (Fase 10)

## Contexto

Síntesis ejecutiva: qué de la validación física puede implementarse YA con el código actual, qué está bloqueado, y en qué orden ejecutar.

## TL;DR — Estado actual

| Métrica | Valor |
|---------|-------|
| Reglas definidas | 53 |
| Reglas implementables hoy con confidence high | 34 |
| Reglas confidence medium (parciales) | 11 |
| Reglas confidence low (gaps de modelo) | 8 |
| Reglas bloqueadas (L-PV-02 faults) | 5 |
| Casos físicos definidos | 30 |
| Experimentos controlados definidos | 19 |
| Datasets de validación definidos | 10 |
| Score interno preliminar estimado | **0.94** (banda "plausible con caveats") |

**El generador está usable** para entrenar modelos ML, con los caveats explícitos de los gaps L-PV-02, L-PV-06, L-PV-07, L-PV-09.

## Qué se puede implementar YA (sin bloqueadores)

### Prioridad 1 — Validador post-run (Opción B)

```yaml
task: T-PV-01
title: Implementar bms_physics_validator paquete + validate_csv_long()
why: |
  Habilita validación de Casos B, C, D (dump-based). Es la Opción B de `07-*`,
  el cambio menos invasivo y más alto-valor.
files_to_create:
  - extensions/bms_physics_validator/pyproject.toml
  - extensions/bms_physics_validator/src/bms_physics_validator/__init__.py
  - extensions/bms_physics_validator/src/bms_physics_validator/types.py        # ValidationReport, RuleResult, RuleSpec
  - extensions/bms_physics_validator/src/bms_physics_validator/scheduler.py
  - extensions/bms_physics_validator/src/bms_physics_validator/scorer.py        # RealismScorer
  - extensions/bms_physics_validator/src/bms_physics_validator/post_run.py      # validate_csv_long
  - extensions/bms_physics_validator/src/bms_physics_validator/rules/__init__.py
  - extensions/bms_physics_validator/src/bms_physics_validator/rules/thermal.py # R-T-01..05
  - extensions/bms_physics_validator/src/bms_physics_validator/rules/co2.py     # R-CO2-01..05
  - extensions/bms_physics_validator/src/bms_physics_validator/rules/humidity.py
  - extensions/bms_physics_validator/src/bms_physics_validator/rules/hvac.py
  - extensions/bms_physics_validator/src/bms_physics_validator/rules/occupancy.py
  - extensions/bms_physics_validator/src/bms_physics_validator/rules/energy.py
  - extensions/bms_physics_validator/src/bms_physics_validator/rules/weather.py
  - extensions/bms_physics_validator/src/bms_physics_validator/rules/anomalies.py
  - extensions/bms_physics_validator/src/bms_physics_validator/rules/infrastructure.py
  - extensions/bms_physics_validator/src/bms_physics_validator/rules/faults.py  # skipped si L-PV-02
  - extensions/bms_physics_validator/tests/unit/test_*.py (1 por familia)
  - extensions/bms_physics_validator/tests/integration/test_post_run.py
  - extensions/bms_physics_validator/tests/golden/baseline_7d_passes.json
files_to_modify:
  - pyproject.toml (raíz): añadir extensions/bms_physics_validator a workspace members
  - .github/workflows/ci.yml: añadir job test-physics que corra pytest sobre nuevo paquete
priority: HIGH
estimated_size: ~2000 LOC + tests.
unblocks: validación de D-PV-02, D-PV-03 (parcial), D-PV-04, D-PV-05, D-PV-06.
```

### Prioridad 2 — Validador live (Opción A)

```yaml
task: T-PV-02
title: ValidatingSink wrapper para live mode
why: |
  Cubre Caso A (live IoT). Permite alertas tiempo real vía Prometheus.
files_to_create:
  - extensions/bms_physics_validator/src/bms_physics_validator/sink_wrapper.py
files_to_modify:
  - modules/bms-data-generator/src/bms_data_generator/services/runner_service.py:91-101
    (envolver cada sink con ValidatingSink si BMS_PHYSICS_VALIDATION_ENABLED=true)
  - modules/bms-data-generator/src/bms_data_generator/config.py
    (añadir physics_validation_enabled, physics_validation_window_seconds)
priority: MEDIUM (después de T-PV-01)
unblocks: D-PV-01, D-PV-09.
```

### Prioridad 3 — Métricas Prometheus

```yaml
task: T-PV-03
title: Añadir captia_physics_* a metrics.py
why: |
  Sin estas métricas, los dashboards de `09-*` no tienen datos.
files_to_create:
  - modules/bms-data-generator/src/bms_data_generator/physics_metrics.py
    (registry separado para captia_physics_*)
files_to_modify:
  - modules/bms-data-generator/src/bms_data_generator/main.py:
    importar physics_metrics para que se registren en /metrics endpoint
priority: HIGH (paralelizable con T-PV-01)
unblocks: dashboard, alertas.
```

### Prioridad 4 — InfluxDB nuevo bucket + Flux task

```yaml
task: T-PV-04
title: Bucket physics_metrics + 1ª Flux task (energy_balance_hourly)
files_to_modify:
  - infra/influxdb/init/init_buckets_tasks.sh:67 (añadir create_bucket_if_missing "physics_metrics" "90d")
  - infra/influxdb/init/init_buckets_tasks.sh:81 (añadir physics_validation_hourly al loop)
files_to_create:
  - infra/influxdb/tasks/physics_validation_hourly.flux
  - infra/influxdb/tasks/physics_co2_slope_hourly.flux
  - infra/influxdb/tasks/physics_hvac_cycle_hourly.flux
priority: MEDIUM
unblocks: dashboard panels 3, 5, 6, 7.
```

### Prioridad 5 — Grafana dashboard

```yaml
task: T-PV-05
title: bms_physics_validation.json dashboard
files_to_create:
  - infra/grafana/dashboards/bms_physics_validation.json
priority: MEDIUM (after T-PV-03 + T-PV-04)
unblocks: visualización.
```

### Prioridad 6 — Alertas Prometheus

```yaml
task: T-PV-06
title: Alert + recording rules para captia_physics_*
files_to_create:
  - infra/prometheus/rules/bms_physics_alerts.rules.yml
  - infra/prometheus/rules/bms_physics_recording.rules.yml
files_to_modify:
  - infra/prometheus/prometheus.yml (referenciar nuevos rule files)
priority: MEDIUM
```

### Prioridad 7 — Wire calibration_loader (cierra L-PV-04)

```yaml
task: T-PV-07
title: Invocar load_faults_config() y load_physics_overrides() en runner
why: cierra L-PV-04 (dead-code) y prepara terreno para T-PV-08 / T-PV-09.
files_to_modify:
  - modules/bms-data-generator/src/bms_data_generator/services/runner_service.py:_build_runner
    (cargar faults_config si BMS_FAULTS_ENABLED, pasar a ScenarioRunner)
priority: HIGH (cheap, alta señal/coste).
unblocks: condición previa a T-PV-08.
```

### Prioridad 8 — FaultEventSink (cierra L-PV-02)

```yaml
task: T-PV-08
title: Materializar FaultEvent → captia_point en state_events
why: |
  Resuelve L-PV-02. Activa todas las R-FAULT-* y D-PV-03 / D-PV-08.
  Es el cambio de mayor impacto en el score (+0.10 estimado).
files_to_create:
  - extensions/bms_calibration/src/bms_calibration/fault_event_sink.py
    (clase que mapea FaultEvent a DataPoint(variable=fault.<tipo>, value=1|0))
files_to_modify:
  - modules/bms-data-generator/src/bms_data_generator/services/runner_service.py
    (instanciar FaultInjector, FaultEventSink, integrar en CompositeSink)
  - extensions/bms_calibration/src/bms_calibration/faults.py
    (la función inject() ya devuelve eventos correctos; solo falta sink)
priority: HIGH
unblocks: R-FAULT-01..05, D-PV-03 completo, D7 dimensión scored.
```

### Prioridad 9 — Unificar calendario (cierra L-PV-06)

```yaml
task: T-PV-09
title: Wire ValenciaSchoolCalendar en path de generación
why: |
  Resuelve L-PV-06. Permite que occupancy=0 en períodos vacacionales reales.
options:
  A: invocar ValenciaSchoolCalendar.is_lectivo() en BMSDomainPlugin (PATCH vendor)
  B: añadir todas las fechas de _BREAKS_2025_2026 a config/domains/bms_classrooms/domain.yaml
recommendation: Opción B (no toca vendor).
files_to_modify:
  - config/domains/bms_classrooms/domain.yaml (línea 9-17): expandir holidays
priority: HIGH (cheap)
unblocks: R-OCC-01 con confianza alta, D-PV-07 produce el resultado esperado.
```

### Prioridad 10 — Generar relay_1..relay_4

```yaml
task: T-PV-10
title: Alimentar relay_1..relay_4 desde physics
why: |
  Cierra sub-issue de L-PV-01 (catálogo coverage R-INF-03).
options:
  A: vincular relays a hvac_enable, light_state, ... (modelo trivial)
  B: dejarlos a 0 documentando que son spare
recommendation: Opción A — vincular relay_1=hvac_enable, relay_2=light_state, etc.
files_to_modify:
  - vendor/.../physics/actuators.py (PATCH)
  - vendor/.../domains/bms_classrooms/plugin.py (output extra series)
priority: LOW (cosmético)
unblocks: R-INF-03 pass (D10 a 1.00).
```

## Qué requiere cambios estructurales (futuro v2)

### Modelo HVAC con cooling explícito (cierra L-PV-08)

```yaml
task: T-PV-11 (futuro)
why: |
  Modelo actual trata heat y cool simétricamente en simulate_indoor_temperature.
  En realidad cooling tiene curva de capacidad vs T_outdoor.
files_to_modify:
  - vendor/.../physics/indoor.py:13-57 (PATCH)
  - vendor/.../physics/energy.py:11-49 (PATCH para diferenciar consumo cool vs heat)
priority: LOW (medio-largo plazo)
risk: rompería tests snapshot existentes.
```

### Modelo humedad con dehumidification (cierra L-PV-09)

```yaml
task: T-PV-12 (futuro)
why: |
  HVAC en cool deshumidifica. Modelo actual ignora.
files_to_modify:
  - vendor/.../physics/indoor.py:102-136 (PATCH añadir término -alpha_dehumid·hvac_enable·cool)
priority: MEDIUM-LOW
```

### Anti short-cycle HVAC (cierra L-PV-07)

```yaml
task: T-PV-13 (futuro)
why: |
  Modelo actual permite toggling sample-a-sample.
files_to_modify:
  - vendor/.../physics/actuators.py:121-146 (PATCH integrar MinOnOffTimer de control_utils.py)
priority: MEDIUM
```

### PerturbationEngine para perturbaciones transport (cierra L-PV-14)

```yaml
task: T-PV-14 (futuro)
why: |
  PerturbationsConfig existe en core/config.py pero no se aplica.
files_to_create:
  - vendor/.../core/perturbations.py (PATCH análogo a anomalies.py)
files_to_modify:
  - vendor/.../core/runner.py (invocar PerturbationEngine después de AnomalyEngine)
priority: LOW
```

### Anomalías adicionales: stuck, drift, offset, duplicates (parcial L-PV-15)

```yaml
task: T-PV-15 (futuro)
files_to_modify:
  - vendor/.../core/anomalies.py:21-110 (extender AnomalyEngine)
priority: LOW
```

## Qué NO debe implementarse todavía

- **Score externo con ground-truth real**: bloqueado por L-01. Esperar datos reales IES Simarro.
- **Curva capacidad cooling vs T_outdoor**: requiere calibración real.
- **PIController en HVAC**: el modelo threshold actual es "good enough" para v1; PI requiere tuning con datos reales.
- **Variación por aula** (orientación, masa térmica diferente): post v1, requiere modelo de edificio.
- **Meteo real** (ERA5): fuera de v1 (L-10 en specs padre).
- **Anonimización dump real**: no aplica (dump sintético puro v1, L-11).

## Tests prioritarios

Por orden de implementación:

1. `test_post_run_validator_smoke.py` — validate_csv_long sobre fixture pequeño funciona.
2. `test_rules_thermal.py` — fixture sintética con violación obvia → R-T-01 fails; sin violación → passes.
3. `test_rules_co2.py` — fixture con buildup conocido → R-CO2-01 mide pendiente correctamente.
4. `test_realism_scorer.py` — agregación correcta, dimensiones blocked unscored.
5. `test_validating_sink.py` — wrapper no rompe path live.
6. `test_metrics_emission.py` — captia_physics_* aparecen en /metrics.
7. `test_d_pv_05_baseline.py` — D-PV-05 produce score ≥ 0.85 (golden test).
8. `test_d_pv_07_diagnoses_l_pv_06.py` — D-PV-07 falla R-OCC-01 si holidays no están unificados (REGRESSION test del bug de calendario).

## Tabla de trazabilidad cruzada

| Regla (`04-*`) | Pregunta (`02-*`) | Caso (`03-*`) | Experimento (`05-*`) | Dataset (`06-*`) | Métrica (`09-*`) |
|---|---|---|---|---|---|
| R-T-01 | PQ-01 | C-TH-01 | Exp-TH-1 | D-PV-05 | physics.thermal_response_tau_min |
| R-T-02 | PQ-02 | C-TH-01 | Exp-TH-2 | D-PV-05 | physics.thermal_response_tau_min |
| R-T-03 | PQ-04 | C-TH-02 | Exp-TH-1 | D-PV-05 | rule_evidence convergence_error |
| R-T-04 | PQ-03 | C-TH-03 | Exp-TH-3 | D-PV-10 | rule_evidence occupancy_temp_correlation |
| R-T-05 | — | — | Exp-HV-2 | D-PV-05 | rule_evidence steady_state_std |
| R-CO2-01 | PQ-10 | C-OC-02 | Exp-IAQ-1 | D-PV-04 | physics.co2_slope_per_occupancy_ppm_min_person |
| R-CO2-02 | PQ-11 | C-OC-03 | Exp-IAQ-1 | D-PV-04 | rule_evidence co2_slope_post_vs_pre |
| R-CO2-03 | PQ-12 | C-OC-04 | Exp-IAQ-2 | D-PV-04 | rule_evidence co2_post_6h_idle |
| R-CO2-04 | — | — | — | D-PV-04 | rule_evidence co2_saturation_ratio |
| R-CO2-05 | — | — | — | D-PV-01 | rule_evidence co2_below_outdoor_count |
| R-RH-01 | — | — | — | D-PV-04 | rule_evidence humidity_out_of_range_count |
| R-RH-02 | — | — | — | D-PV-04 | physics.cooling_dehumid_slope_pct_min |
| R-RH-03 | — | — | — | D-PV-04 | rule_evidence rh_occupancy_correlation |
| R-N-01 | PQ-13 | — | — | D-PV-05 | rule_evidence noise_jump_count |
| R-LX-01 | — | — | — | D-PV-05 | rule_evidence indoor_lt_daylight_count |
| R-LX-02 | — | — | — | D-PV-05 | rule_evidence light_state_consistency |
| R-LS-01 | — | — | — | D-PV-05 | rule_evidence light_on_empty_count |
| R-PIR-01 | — | — | — | D-PV-05 | rule_evidence pir_fp_rate, pir_fn_rate |
| R-SC-01 | — | — | — | D-PV-05 | rule_evidence scene_class_consistency |
| R-SP-01 | — | — | — | D-PV-05 | rule_evidence setpoint_out_of_range_count |
| R-HVAC-MODE-01 | PQ-06 | C-HV-02 | Exp-HV-1 | D-PV-02 | rule_evidence hvac_mode_consistency_per_outdoor_bucket |
| R-HVAC-EN-01 | PQ-05 | C-HV-01 | Exp-HV-2 | D-PV-05 | rule_evidence hvac_enable_accuracy |
| R-HVAC-EN-02 | PQ-09 | — | Exp-HV-2 | D-PV-05 | rule_evidence power_diff_hvac_on_off |
| R-HVAC-EN-03 | PQ-07 | C-HV-03 | Exp-HV-2 | D-PV-05 | physics.hvac_short_cycle_ratio |
| R-VLV-01 | PQ-08 | C-HV-04 | — | D-PV-05 | rule_evidence valve_mode_inconsistency_count |
| R-VLV-02 | — | — | — | D-PV-05 | rule_evidence valve_max_diff_per_min |
| R-OCC-01 | PQ-14 | C-OC-01 | Exp-CAL-1 | D-PV-07 | physics.occupancy_holiday_mean |
| R-OCC-02 | PQ-15 | C-OC-01 | Exp-CAL-2 | D-PV-02 | rule_evidence occupancy_slot_compliance |
| R-OCC-03 | — | — | — | D-PV-05 | rule_evidence occupancy_above_capacity_count |
| R-PW-01 | PQ-16 | C-EN-02 | — | D-PV-05 | rule_evidence power_decomposition_r_squared |
| R-PW-02 | PQ-19 | C-EN-03 | — | D-PV-05 | rule_evidence power_idle_median |
| R-PW-03 | — | — | — | D-PV-05 | rule_evidence power_negative_count |
| R-EN-01 | PQ-17 | C-EN-01 | — | D-PV-02 | physics.energy_balance_error_pct |
| R-EN-02 | PQ-18 | C-EN-01 | — | D-PV-02 | rule_evidence energy_decreasing_count |
| R-EN-03 | — | — | — | D-PV-02 | rule_evidence daily_energy_kwh_mean |
| R-OT-01 | PQ-22 | C-WX-01 | — | D-PV-02 | rule_evidence outdoor_jump_count |
| R-OT-02 | — | — | — | D-PV-02 | rule_evidence outdoor_out_of_range_count |
| R-DL-01 | PQ-24 | C-WX-03 | — | D-PV-02 | rule_evidence daylight_day_night_consistency |
| R-WX-01 | PQ-23 | C-WX-02 | Exp-WX-1 | D-PV-02 | rule_evidence seasonal_amplitude |
| R-WD-01 | PQ-20 | C-EN-04 | — | D-PV-02 | rule_evidence energy_severity_correlation |
| R-FAULT-01 | PQ-26 | C-FA-01 | Exp-FA-1 | D-PV-03 | physics.fault_signature_match (sensor_drift) |
| R-FAULT-02 | PQ-27 | C-FA-02 | Exp-FA-2 | D-PV-03 | physics.fault_signature_match (valve_stuck) |
| R-FAULT-03 | PQ-28 | C-FA-03 | Exp-FA-3 | D-PV-03 | physics.fault_signature_match (fan_failure) |
| R-FAULT-04 | PQ-29 | C-FA-04 | — | D-PV-03 | physics.fault_signature_match (refrigerant_low) |
| R-FAULT-05 | PQ-30 | — | — | D-PV-03 | rule_evidence fault_event_coverage |
| R-AN-01 | PQ-31 | C-AN-01 | Exp-AN-1 | D-PV-09 | rule_evidence missing_rate_observed |
| R-AN-02 | PQ-32 | C-AN-02 | Exp-AN-2 | D-PV-09 | rule_evidence outlier_rate_observed |
| R-AN-03 | PQ-33 | C-AN-03 | Exp-AN-3 | D-PV-09 | rule_evidence burst_distribution_match |
| R-INF-01 | PQ-35 | C-CO-01 | Exp-INF-2 | D-PV-01 | (vía verify_canonical_schema.sh) |
| R-INF-02 | PQ-25 | C-CO-02 | Exp-INF-1 | D-PV-01 | (vía snapshot test) |
| R-INF-03 | PQ-37,38 | C-CO-03 | — | D-PV-01 | rule_evidence catalog_coverage_ratio |
| R-INF-04 | PQ-39 | — | — | D-PV-01 | rule_evidence freq_compliance |
| R-INF-05 | PQ-40 | — | Exp-INF-3 | D-PV-09 | rule_evidence dst_handling_correct |

## Roadmap propuesto

| Sprint | Tasks | Outcome |
|--------|-------|---------|
| Sprint 1 (1-2 semanas) | T-PV-03, T-PV-07, T-PV-09 | Métricas Prometheus listas; calibration_loader cableado; calendario unificado. |
| Sprint 2 (2-3 semanas) | T-PV-01 | Validador post-run completo + tests. Score interno calculable. |
| Sprint 3 (1-2 semanas) | T-PV-04, T-PV-05, T-PV-06 | InfluxDB bucket + Flux tasks + dashboard + alertas. |
| Sprint 4 (1-2 semanas) | T-PV-02 | ValidatingSink live + tests. Caso A cubierto. |
| Sprint 5 (1 semana) | T-PV-08 | FaultEventSink. R-FAULT-* activas. Score sube ~0.10. |
| Sprint 6 (opcional) | T-PV-10 | Generar relays. R-INF-03 pass. |
| Sprint v2 | T-PV-11..15 | Mejoras estructurales del modelo (cooling explícito, dehumidification, anti-cycle, perturbations, anomalías ext.). |

## Cómo cerrar este spec set

Cuando los Sprints 1-5 estén completos:

- Score interno proyectado: **~0.97** (de 0.94 actual).
- Score externo: aún N/A hasta L-01.
- Las 53 reglas: 48 con confidence ≥ medium activas (vs 34 hoy).
- D7 dimensión scored.
- Documentar en `STATUS.md` el avance de cada sprint.
- Cuando llegue L-01 (calibración real): añadir spec `11-calibrated-validation.md` (futuro), no modificar las existentes.

## Cross-references a actualizar (PROPUESTAS, NO aplicadas en este spec set)

Estas modificaciones a specs existentes se PROPONEN pero NO se aplican aquí (mantener este spec set autocontenido):

| Fichero | Cambio propuesto |
|---------|------------------|
| `docs/specs/synthetic-bms/02-domain-spec.md:60-85` | Rectificar variables al catálogo real (`temperature` no `temperature_01`, etc.) y eliminar las inexistentes. Añadir nota: "Para validación física ver `docs/specs/digital-twin-bms-physics-validation/`." |
| `docs/specs/synthetic-bms/00-open-questions.md` | Marcar L-01 como "Tracked en physics-validation L-PV-* y `08-physical-realism-score.md` (score externo)." |
| `docs/specs/synthetic-bms/05-observability-spec.md` | Añadir sección "Physics validation observability — ver `docs/specs/digital-twin-bms-physics-validation/09-*`." |
| `docs/specs/synthetic-bms/09-decision-log.md` | Añadir ADR-016 cuando se cablee FaultEventSink (T-PV-08). |
| `docs/specs/synthetic-bms/STATUS.md` (post-pub pendientes) | Añadir línea: "Physics validation framework — ver docs/specs/digital-twin-bms-physics-validation/". |
| `CLAUDE.md` | Considerar añadir línea breve: "Validación física: docs/specs/digital-twin-bms-physics-validation/." |
| `infra/influxdb/init/init_buckets_tasks.sh:67` | Insertar create_bucket_if_missing "physics_metrics" "90d". |
| `pyproject.toml` (raíz) | Añadir extensions/bms_physics_validator a workspace members. |
| `Makefile` / `Taskfile.yml` | Añadir `make test-physics`, `make validate-dump`. |
| `.github/workflows/ci.yml` | Añadir job `test-physics` que corra pytest sobre nuevo paquete. |

## Recomendación final

**Empezar por T-PV-09 (calendario unificado)** porque:
- Es el cambio más barato (1 línea de YAML).
- Cierra L-PV-06 con confidence alta.
- Hace que D-PV-07 dataset detecte el caso correcto.
- Es validable inmediatamente con una run de Caso B en período Navidad.

**Seguir por T-PV-07 → T-PV-08** (wire calibration_loader → FaultEventSink): juntos cierran L-PV-04 y L-PV-02, los gaps más importantes. Sin esto, Caso C real es imposible.

**Después** T-PV-01 + T-PV-03 en paralelo (validator post-run + métricas) habilitan los dashboards y reportes.

Con ese plan, en ~6-8 semanas el generador pasa de "plausible con caveats" (score 0.94) a "plausible robusto" (score ≥ 0.97 + R-FAULT-* activas).
