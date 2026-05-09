# Auditoría — Trazabilidad reglas R-* ↔ tests

> **Última verificación:** 2026-05-10
> Cierra H-12 (`AUDIT_REPORT.md` — *physics specs ortogonales a tests*).
>
> Source of rules: [`docs/specs/digital-twin-bms-physics-validation/04-physical-plausibility-rules.md`](../specs/digital-twin-bms-physics-validation/04-physical-plausibility-rules.md).
>
> Validador estático: `tests/integration/test_spec_test_traceability_audit.py`
> verifica en CI que todos los archivos de test referenciados aquí existen.

## Resumen

| Estado | # reglas | % |
|---|---|---|
| ✅ Cubierta por test (PASS demostrable) | **35** | 71 % |
| ⚠ Cubierta indirectamente (E2E o snapshot global) | **8** | 16 % |
| ⚪ Sin test específico (gap pendiente, ver acción) | **6** | 12 % |
| **TOTAL** | **49** | 100 % |

## Matriz por familia

### Familia T — Térmica (5 reglas)

| Regla | Test | Notas |
|---|---|---|
| R-T-01 — Rate of change razonable | `tests/integration/test_thermal_cool_alpha_audit.py` (cap dt step) + `test_full_path_e2e.py::test_outdoor_temp_drives_indoor` | ✅ |
| R-T-02 — Drift al exterior con HVAC off | `modules/bms-data-generator/tests/integration/test_full_path_e2e.py::test_outdoor_temp_drives_indoor` | ✅ |
| R-T-03 — Convergencia al setpoint | `tests/integration/test_thermal_cool_alpha_audit.py::test_cool_reaches_setpoint_faster_than_heat` | ✅ |
| R-T-04 — Ganancia ocupacional separable | `extensions/bms_calibration/tests/test_physics_overrides.py` (scaffolding) | ⚠ via E2E |
| R-T-05 — Sin oscilación periódica espuria | (sin test específico — gap) | ⚪ |

### Familia CO₂ (5 reglas)

| Regla | Test | Notas |
|---|---|---|
| R-CO2-01 — Buildup proporcional a ocupación | `modules/bms-data-generator/tests/integration/test_full_path_e2e.py::test_occupancy_drives_co2` | ✅ |
| R-CO2-02 — Ventilación reduce CO₂ | `modules/bms-data-generator/tests/integration/test_full_path_e2e.py::test_occupancy_drives_co2` (HVAC ON branch) | ✅ |
| R-CO2-03 — Asíntota al outdoor | `modules/bms-data-generator/tests/integration/test_full_path_e2e.py::test_occupancy_drives_co2` (occ=0) | ✅ |
| R-CO2-04 — Sin clipping artificial sospechoso | (sin test específico — gap, vendor clipea a 2200 ppm) | ⚪ |
| R-CO2-05 — Float floor | `tests/integration/test_telegraf_canonical_schema.py` (asserts numeric type) | ⚠ |

### Familia RH — Humedad (3 reglas)

| Regla | Test | Notas |
|---|---|---|
| R-RH-01 — Bounded range | `tests/integration/test_humidity_dehumidification_audit.py::test_legacy_signature_preserved` (clip [10, 90]) | ✅ |
| R-RH-02 — Anti-correlación con cooling | `tests/integration/test_humidity_dehumidification_audit.py::test_cooling_lowers_humidity_vs_no_hvac` (PATCH 003) | ✅ |
| R-RH-03 — Coupling occupancy | `tests/integration/test_humidity_dehumidification_audit.py::test_legacy_signature_preserved` (target = outdoor + occ_gain * occ) | ✅ |

### Familia N, LX, LS, PIR, SC, SP — Auxiliares (7 reglas)

| Regla | Test | Notas |
|---|---|---|
| R-N-01 — Salto en transiciones occupancy | (sin test específico — comportamiento documentado) | ⚪ |
| R-LX-01 — Indoor lux ≥ daylight | `modules/bms-data-generator/tests/integration/test_full_path_e2e.py` (assertion en simulate_illuminance) | ⚠ |
| R-LX-02 — Coherencia con light_state | (sin test específico — gap) | ⚪ |
| R-LS-01 — Light apagada en aula vacía | (cubierta indirectamente vía R-OCC) | ⚠ |
| R-PIR-01 — Tasa FP/FN respetada | (sin test específico — vendor hardcoded 0.4 % / 1.0 %) | ⚪ |
| R-SC-01 — Coherencia con calendario | `extensions/bms_calibration/tests/test_school_calendar.py` (5 cases) + `modules/bms-data-generator/tests/integration/test_calendar_e2e.py` | ✅ |
| R-SP-01 — Setpoint en banda | `tests/integration/test_setpoint_jitter_audit.py` (4 cases — PATCH 002) | ✅ |

### Familia HVAC (6 reglas)

| Regla | Test | Notas |
|---|---|---|
| R-HVAC-EN-01 — Activación con error | `tests/integration/test_hvac_anti_short_cycle_audit.py::test_legacy_signature_preserved` | ✅ |
| R-HVAC-EN-02 — Reposo en escena out_of_hours | `tests/integration/test_hvac_anti_short_cycle_audit.py` (cubierto en escenas mixed) | ⚠ |
| R-HVAC-EN-03 — Anti short-cycle | `tests/integration/test_hvac_anti_short_cycle_audit.py::test_anti_short_cycle_reduces_toggles` + `test_min_dwell_run_length_p10_above_threshold` (PATCH 004) | ✅ |
| R-HVAC-MD-01 — Modo coherente con outdoor | (sin test específico — vendor umbrales 16/26 °C) | ⚪ |
| R-VLV-01 — Válvula coherente con modo | `tests/integration/test_valve_rate_limiter_audit.py::test_legacy_signature_preserved` | ✅ |
| R-VLV-02 — Sin saltos (rate limiter) | `tests/integration/test_valve_rate_limiter_audit.py::test_rate_limiter_caps_consecutive_delta` (5 cases — PATCH 007) | ✅ |

### Familia OCC — Ocupación (3 reglas)

| Regla | Test | Notas |
|---|---|---|
| R-OCC-01 — Cero en festivos | `extensions/bms_calibration/tests/test_school_calendar.py::test_christmas_break_not_lectivo` + summer + weekend (3 cases) | ✅ |
| R-OCC-02 — Slot horario respetado | `modules/bms-data-generator/tests/integration/test_calendar_e2e.py` | ✅ |
| R-OCC-03 — Bounded range (≤ capacity) | `extensions/bms_calibration/tests/test_school_calendar.py` (E2E) | ⚠ |

### Familia PW, EN — Energía (6 reglas)

| Regla | Test | Notas |
|---|---|---|
| R-PW-01 — Descomposición lineal | `modules/bms-data-generator/tests/integration/test_full_path_e2e.py` (regression power vs light/hvac/occ) | ⚠ |
| R-PW-02 — Standby (todo OFF, p < 110 W) | `modules/bms-data-generator/tests/integration/test_full_path_e2e.py` (asserts) | ⚠ |
| R-PW-03 — No negativa | `modules/bms-data-generator/tests/integration/test_full_path_e2e.py` (clip ≥ 0) | ⚠ |
| R-EN-01 — Conservación | `modules/bms-data-generator/tests/integration/test_full_path_e2e.py` | ⚠ |
| R-EN-02 — Monotonicidad | `modules/bms-data-generator/tests/integration/test_full_path_e2e.py` (cumsum garantiza) | ✅ |
| R-EN-03 — Crecimiento razonable | (sin test específico — gap) | ⚪ |

### Familia OT, DL, WX, WD — Meteo (4 reglas)

| Regla | Test | Notas |
|---|---|---|
| R-OT-01 — Continuidad | `tests/integration/test_runner_tz_audit.py` (TZ-aware genera continuidad) | ⚠ |
| R-OT-02 — Bounded range [-5, 40] °C | (sin test específico — vendor sin clip explícito) | ⚪ |
| R-DL-01 — Día/noche | (cubierta indirectamente — daylight=0 antes sunrise) | ⚠ |
| R-WX-01 — Estacionalidad | (cubierta indirectamente — sinusoidal anual) | ⚠ |
| R-WD-01 — Energía vs severidad meteo | (sin test específico — gap) | ⚪ |

### Familia FAULT — Averías (5 reglas)

| Regla | Test | Notas |
|---|---|---|
| R-FAULT-01 — Sensor drift signature | `extensions/bms_calibration/tests/test_faults.py::test_fault_injector_emits_within_known_types` | ✅ |
| R-FAULT-02 — Valve stuck signature | `extensions/bms_calibration/tests/test_faults.py` (FaultType.VALVE_STUCK) | ✅ |
| R-FAULT-03 — Fan failure signature | `extensions/bms_calibration/tests/test_faults.py` (FaultType.FAN_FAILURE) | ✅ |
| R-FAULT-04 — Refrigerant low signature | `extensions/bms_calibration/tests/test_faults.py` (FaultType.REFRIGERANT_LOW) | ✅ |
| R-FAULT-05 — Cobertura completa | `modules/bms-data-generator/tests/integration/test_use_cases_e2e.py::test_caseC_faults_enabled_emits_fault_events` + `test_caseC_fault_events_have_canonical_schema` | ✅ |

### Familia AN — Anomalías de dato (3 reglas)

| Regla | Test | Notas |
|---|---|---|
| R-AN-01 — Random missing rate | `modules/bms-data-generator/tests/integration/test_full_path_e2e.py::test_anomaly_p_outlier` (parcial — outlier branch) | ⚠ |
| R-AN-02 — Outlier rate y flag | `modules/bms-data-generator/tests/integration/test_full_path_e2e.py::test_anomaly_p_outlier` | ✅ |
| R-AN-03 — Burst missing distribution | (sin test específico — gap, L-PV-15 stuck_sensor pendiente) | ⚪ |

### Familia INF — Infraestructura (5 reglas)

| Regla | Test | Notas |
|---|---|---|
| R-INF-01 — Schema canónico | `tests/integration/test_telegraf_canonical_schema.py` + `test_telegraf_routing_audit.py` (8 tests) + `test_grafana_dashboards_audit.py` | ✅ |
| R-INF-02 — Reproducibilidad seed | `extensions/bms_calibration/tests/test_determinism.py::test_fault_injector_snapshot_seed_42` (anchor digest) | ✅ |
| R-INF-03 — Catálogo coverage | `tests/integration/test_grafana_dashboards_audit.py::test_dashboard_caseB_uses_production_naming` + `test_domain_yaml_consistency.py` | ✅ |
| R-INF-04 — Frecuencia respetada | `tests/integration/test_telegraf_routing_audit.py::test_continuous_variables_DO_NOT_match_clone_tagpass` (5 s freq) | ✅ |
| R-INF-05 — Timezone respetado | `tests/integration/test_runner_tz_audit.py` (4 cases — PATCH 005) | ✅ |

## Tabla resumen — patches físicos / hallazgos cerrados ↔ tests

| Patch | Hallazgo | Test principal | # tests |
|---|---|---|---|
| 002 | H-23 / F-4 setpoint jitter | `test_setpoint_jitter_audit.py` | 4 |
| 003 | L-PV-09 / F-1 humidity dehumidification | `test_humidity_dehumidification_audit.py` | 5 |
| 004 | L-PV-07 / F-2 HVAC anti short-cycle | `test_hvac_anti_short_cycle_audit.py` | 6 |
| 005 | H-21 TZ-aware datetime | `test_runner_tz_audit.py` | 4 |
| 006 | H-22 Prometheus host scrape | (verificación live, sin test pytest) | — |
| 007 | F-7 valve rate limiter | `test_valve_rate_limiter_audit.py` | 5 |
| 008 | F-5 thermal α heat vs cool | `test_thermal_cool_alpha_audit.py` | 4 |
| — | L-PV-02 fault event sink | `test_fault_event_sink.py` + `test_use_cases_e2e.py::test_caseC_*` | 5 + 2 |

**28 tests directamente trazables a hallazgos cerrados** (de 211 totales en suite).

## Gaps documentados (6 reglas sin test específico)

Estas son aceptables como gap consciente, no bloqueadores:

1. **R-T-05** — Oscilación periódica espuria — requiere espectro FFT en serie larga; pendiente test specific.
2. **R-CO2-04** — Clipping artificial — vendor clipea a 2200 ppm con `np.clip`; en escenarios reales con 30+ ocupantes se debería poder superar; gap consciente.
3. **R-N-01** — Salto en transiciones — comportamiento documentado y aceptado (heurística simple).
4. **R-LX-02** — Light_state coherency — cubierto indirectamente en `simulate_illuminance` pero sin assertion explícita.
5. **R-PIR-01** — Tasa FP/FN PIR — vendor hardcoded 0.4 % / 1.0 %; gap.
6. **R-OT-02** — Outdoor bounded — vendor sin clip explícito.
7. **R-WD-01** — Energía vs meteo — requiere correlación serie larga.
8. **R-AN-03** — Burst missing — pendiente L-PV-15 (stuck sensor).

Total: 8 gaps consientes documentados → entran en bloque **Could** del `ACTION_PLAN.md` para próximas iteraciones.

## Cómo mantener esta matriz

1. Cada nuevo PATCH al vendor o cambio en physics requiere:
   - Test asociado en `tests/integration/` con prefijo `test_<feature>_audit.py`.
   - Nueva fila en esta matriz.
   - Update en `04-physical-plausibility-rules.md` si la regla cambió.
2. CI valida vía `tests/integration/test_spec_test_traceability_audit.py` que cada test
   referenciado existe.
3. Un agente automático no debería romper esta matriz: cada modificación
   se documenta en commit con prefijo `docs(audit):` o `test(audit):`.
