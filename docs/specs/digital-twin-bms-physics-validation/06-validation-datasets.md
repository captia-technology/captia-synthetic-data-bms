# 06 — Datasets de validación física (Fase 6)

## Contexto

Catálogo de datasets que el generador debe poder producir para alimentar el validador (`07-*`). Se construyen sobre los 4 escenarios existentes (`config/projects/bms_v1_*.yaml`) más nuevos baselines diseñados para revelar comportamientos físicos específicos.

**Convención de IDs**: `D-PV-NN`. Cada dataset tiene un `purpose` claro y `expected_validation_passes`/`failures` para que el resultado sea predecible.

## Datasets sobre escenarios existentes

### D-PV-01 — Baseline Caso A live

```yaml
dataset_id: D-PV-01
based_on: config/projects/bms_v1_demo.yaml
purpose: |
  Validación inicial del path live MQTT. Verifica schema canónico, frecuencia 5s,
  conexión Mosquitto/Telegraf/Influx end-to-end.
duration: 30 días (Sep 8 → Oct 8 2025).
seed: 42
context:
  - n_aulas: 10
  - frequency: 5 s
  - sinks: [MQTT]
enabled_faults: []
enabled_anomalies: {p_missing: 0.001, p_outlier: 0.001, burst_missing_prob_per_day: 0}
expected_physical_patterns:
  - C-OC-01 (occupancy en horario lectivo)
  - C-OC-02 (CO₂ buildup proporcional)
  - C-EN-01 (conservación power → energy)
  - C-EN-02 (descomposición power)
expected_validation_passes:
  - R-INF-01 (schema)
  - R-INF-02 (reproducibilidad seed)
  - R-CO2-01, R-CO2-02 (coupling occupancy)
  - R-PW-01, R-PW-03
  - R-EN-01, R-EN-02
expected_validation_failures: []
expected_diagnostic_findings:
  - R-HVAC-EN-03 (short-cycle ratio puede ser alto — L-PV-07)
  - R-RH-02 (cooling no deshumidifica — L-PV-09)
notes: |
  Es el dataset "smoke + plausibilidad". Si falla algo aquí, es estructural.
```

### D-PV-02 — Baseline Caso B 12 meses consumption

```yaml
dataset_id: D-PV-02
based_on: config/projects/bms_v1_caseB_consumption.yaml
purpose: |
  Validación de patrones a largo plazo. Estacionalidad meteo, consumo eléctrico anual,
  comportamiento en transiciones estacionales y vacaciones.
duration: 365 días (Sep 1 2025 → Aug 31 2026).
seed: 42
frequency: 5 min
sinks: [File csv_long]
enabled_faults: []
enabled_anomalies: {}
expected_physical_patterns:
  - C-WX-02 (estacionalidad outdoor_temp)
  - C-EN-04 (consumo escala con clima)
  - C-OC-01 (occupancy lectivo vs vacaciones)
expected_validation_passes:
  - R-OT-01, R-OT-02
  - R-WX-01
  - R-EN-03 (kWh/día razonable)
  - R-OCC-01 (cero en vacaciones — depende de L-PV-06)
expected_validation_failures:
  - Si L-PV-06 (calendario vendor vs ValenciaSchoolCalendar) está sin resolver:
    R-OCC-01 puede fallar para fechas reales (Fallas, Pascua) NO listadas en domain.yaml.
expected_diagnostic_findings:
  - R-WD-01 (energía vs severidad: pendiente positiva pero modesta — modelo HVAC step).
notes: |
  Dataset crítico para Caso B (predicción consumo). Si el patrón estacional no es
  realista, los modelos ML aprenderán mal.
```

### D-PV-03 — Baseline Caso C 6 meses con faults

```yaml
dataset_id: D-PV-03
based_on: config/projects/bms_v1_caseC_faults.yaml
purpose: |
  Validación de detección de averías HVAC. Genera dataset etiquetado para entrenar
  anomaly detectors.
duration: 181 días (Jan 1 → Jun 30 2026).
seed: 42
frequency: 5 min
sinks: [File csv_long]
enabled_faults: [sensor_drift, valve_stuck, fan_failure, refrigerant_low]
faults_config_path: config/domains/bms_classrooms/faults.yaml
enabled_anomalies: {p_missing: 0.0005}
expected_physical_patterns:
  - C-FA-01..04 (firmas de avería)
expected_validation_passes:
  - R-INF-01 (schema)
  - R-AN-01 (missing rate)
expected_validation_failures:
  - R-FAULT-01..05: todas FAIL en estado actual del código (L-PV-02 — FaultEventSink no implementado).
  - state_events bucket vacío para variable=fault.* → cobertura 0%.
expected_diagnostic_findings:
  - count(FaultEvent generados por FaultInjector) > 0 (la generación SÍ funciona).
  - Pero ningún DataPoint con variable=fault.* en sink → wiring perdido.
notes: |
  Este dataset es el TEST DE INTEGRACIÓN clave para L-PV-02. Cuando se resuelva,
  todas las R-FAULT-* deberían pasar.
```

### D-PV-04 — Baseline Caso D 3 meses IAQ 1 min

```yaml
dataset_id: D-PV-04
based_on: config/projects/bms_v1_caseD_iaq.yaml
purpose: |
  Validación granularidad fina de IAQ (CO₂, T, RH, occupancy).
  Predicción de calidad del aire para alertas tempranas.
duration: 92 días (Mar 1 → May 31 2026).
seed: 42
frequency: 1 min
sinks: [File csv_long]
enabled_faults: []
enabled_anomalies: {p_missing: 0.001}
expected_physical_patterns:
  - C-OC-02, C-OC-03 (CO₂ dynamics)
  - C-OC-04 (decadencia nocturna)
expected_validation_passes:
  - R-CO2-01..05
  - R-RH-01 (rango)
  - R-RH-03 (coupling occupancy)
  - R-N-01 (con info severity)
expected_validation_failures:
  - R-RH-02 (anti-correlación con cooling — L-PV-09).
notes: |
  Dataset ideal para validar dinámicas CO₂ con resolución 1 min.
  Span Mar-May incluye Pascua (fines de marzo - principio abril).
```

## Datasets nuevos diseñados para validación física

### D-PV-05 — Baseline estable

```yaml
dataset_id: D-PV-05
new_config: derived_from_demo, override:
  simulation.start: "2026-04-13" (lunes lectivo, primavera moderada)
  simulation.duration: "7 days"
  physics.outdoor_temp.amplitude: 2.0  # bajar variabilidad para baseline limpio
purpose: |
  Baseline "limpio" de 1 semana lectiva con clima moderado constante.
  Sirve como referencia para todos los experimentos pareados.
duration: 7 días
seed: 42
expected_validation_passes: prácticamente todas las reglas high-confidence.
expected_validation_failures: ninguna esperada (excepto los gaps conocidos R-RH-02, R-HVAC-EN-03, R-VLV-02).
notes: |
  Este es el "happy path". Si falla aquí, gap es real, no contextual.
```

### D-PV-06 — Transición de estación

```yaml
dataset_id: D-PV-06
new_config: derived_from_caseB, override:
  simulation.start: "2026-04-15"
  simulation.duration: "60 days"
purpose: |
  Capturar transición primavera→verano. Validar que mode HVAC cambia gradualmente
  de heat a off a cool, sin oscilación.
duration: 60 días
seed: 42
expected_physical_patterns:
  - Cambio gradual hvac_mode con T_outdoor cruzando 16°C y 26°C thresholds.
expected_validation_passes:
  - R-HVAC-MODE-01 (modo coherente con T_outdoor por bucket).
  - R-OT-01 (continuidad).
expected_diagnostic_findings:
  - Frecuencia de cambios mode/día (mide oscilación).
  - Si fluctúa rápido en bordes 16/26, sugiere falta de deadband (gap futuro).
notes: |
  Buena oportunidad para diagnóstico de L-PV-08 (sin diferenciación heat/cool).
```

### D-PV-07 — Día festivo aislado

```yaml
dataset_id: D-PV-07
new_config: derived_from_demo, override:
  simulation.start: "2025-12-22" (inicio Navidad)
  simulation.duration: "16 days" (cubre todo período Navidad+Reyes)
purpose: |
  Validar que durante vacaciones formales (ValenciaSchoolCalendar dice 22-dic → 7-ene):
  - occupancy ≈ 0
  - hvac_enable_duty ≤ 5%
  - power diario ≈ standby × 24h × 60min
duration: 16 días
seed: 42
expected_physical_patterns:
  - Occupancy nula durante todo el período.
expected_validation_passes:
  - R-OCC-01 (cero en vacaciones).
  - R-PW-02 (standby).
expected_validation_failures:
  - **Si L-PV-06 sin resolver**: domain.yaml solo lista 25-dic, 1-ene, 6-ene como holidays.
    Días intermedios (23-dic, 24-dic, 26-dic, etc.) tendrán occupancy > 0
    porque school_mask los considera lectivos (lunes-viernes).
expected_diagnostic_findings:
  - count_dias_con_occupancy_diaria > 1: si > 0, confirma bug L-PV-06.
notes: |
  CRITICAL para detectar L-PV-06. Este dataset es básicamente un test de regresión
  del calendario.
```

### D-PV-08 — Recuperación post-avería (cuando wiring exista)

```yaml
dataset_id: D-PV-08
status: BLOCKED por L-PV-02.
new_config: derived_from_caseC, override:
  faults.valve_stuck.probability_per_day: 0.5  # 1 evento cada 2 días
purpose: |
  Validar que tras un episodio de avería, el sistema vuelve al comportamiento normal.
duration: 14 días
expected_physical_patterns:
  - 7 episodios valve_stuck a lo largo de 14 días.
  - Tras cada episodio: válvula responde de nuevo a (setpoint - T).
expected_validation_passes:
  - R-FAULT-02 (signature durante episodio).
  - Recovery: std(valve_pos) post-episodio == std normal.
expected_validation_failures:
  - Mismo bloqueo L-PV-02.
links: L-PV-02
```

### D-PV-09 — Stress test extremo

```yaml
dataset_id: D-PV-09
new_config: derived_from_demo, override:
  n_aulas: 70  # max
  simulation.duration: "1 day"
  anomalies.p_missing: 0.05
  anomalies.p_outlier: 0.02
  anomalies.burst_missing_prob_per_day: 1.0
  faults_enabled: true (cuando wiring exista)
purpose: |
  Stress test del path completo. Verificar que el generador, MQTT, Telegraf, Influx
  no se atascan con 70 aulas, anomalías altas y eventos.
duration: 1 día
expected_physical_patterns:
  - Comportamiento físico válido (no degradación de plausibilidad por stress).
expected_validation_passes:
  - Reglas físicas siguen pasando (R-T-*, R-CO2-*).
  - R-AN-01..03 con magnitudes mayores.
expected_validation_failures:
  - Posibles drops por backpressure Mosquitto (validar que no ocurra; ver tuning F1.1 a 200k queue).
notes: |
  Este dataset valida también la salud del pipeline. Métricas Prometheus relevantes:
  captia_bms_publish_errors_total debe ser 0.
  captia_telegraf_input_messages_received_total debe coincidir con count emitted.
```

### D-PV-10 — Forzado para experimentos pareados

```yaml
dataset_id: D-PV-10
new_config: dataset paramétrico, derivado por exp_id.
purpose: |
  Conjunto de pequeños runs (3-8 horas cada uno) generados específicamente para
  los experimentos en `05-controlled-simulation-validation.md` (pares A/B).
duration: variable por experimento.
seed: 42 por receta.
mechanism: |
  Los experimentos materializan datasets ad-hoc invocando ScenarioRunner con override
  YAML por experimento. Storage temporal en /tmp o RAM-disk; no persistente.
notes: |
  No se almacena en repo; se genera bajo demanda en CI o en sesión dev.
```

## Política de almacenamiento y formato

| Dataset | Formato | Tamaño aprox | Storage | Persistencia |
|---------|---------|--------------|---------|--------------|
| D-PV-01 (live 30d) | MQTT live → Influx telemetry bucket | 70·21·12·24·30 ≈ 13M points | InfluxDB local | volátil (volumen Docker) |
| D-PV-02 (12 meses) | CSV long file | ~2M rows · 21 vars · 10 aulas ≈ 50 GB raw / 10 GB compressed | `output/bms_caseB_consumption_12m.lp` | persiste hasta limpieza manual |
| D-PV-03 (6 meses faults) | CSV long file | ~10 GB | `output/bms_caseC_faults_6m.lp` | persiste |
| D-PV-04 (3 meses IAQ 1min) | CSV long file | ~2.5 GB | `output/bms_caseD_iaq_3m.lp` | persiste |
| D-PV-05 (baseline 7d) | CSV long file | ~50 MB | `output/baseline_7d.lp` | persiste para fixtures |
| D-PV-06 (transición 60d) | CSV long file | ~500 MB | `output/transition_60d.lp` | persiste |
| D-PV-07 (festivo 16d) | CSV long file | ~50 MB | `output/festivo_16d.lp` | persiste para test L-PV-06 |
| D-PV-08 (recuperación 14d) | CSV long file | ~50 MB | bloqueado | n/a |
| D-PV-09 (stress 1d 70 aulas) | MQTT + Influx | ~200k points/min · 1440 min | Influx | volátil |
| D-PV-10 (paramétrico) | Memoria / tmp | variable | volátil | n/a |

## Catálogo de variables esperadas por dataset

Todos los datasets emiten las 21 variables del catálogo `vendor/.../variables.yaml`:
`temperature, humidity, co2, iaq_index, noise, illuminance, occupancy, presence_pir, outdoor_temp, daylight_lux, thermostat_setpoint, hvac_mode, hvac_enable, heating_valve_pos, scene_mode, relay_1, relay_2, relay_3, relay_4, power, energy`.

Excepción: `relay_1..relay_4` están en catálogo pero **no se generan** (gap L-PV-01 sub-issue). Documentado.

## Cómo invocar la generación

| Dataset | Comando |
|---------|---------|
| D-PV-01 | `make up && curl -X POST :8120/v1/control/start -d '{"config_path": "/app/config/projects/bms_v1_demo.yaml", "mode": "live", "aulas": 10, "faults": []}'` |
| D-PV-02 | `make dump-caseB` (ya wireado) |
| D-PV-03 | `make dump-caseC` |
| D-PV-04 | `make dump-caseD` |
| D-PV-05..07, 09 | requieren scripts dedicados (`scripts/dump_baseline.sh`, etc., a crear en `10-implementation-readiness.md`). |
| D-PV-10 | invocado desde experiments_runner (futuro). |

## Trazabilidad caso → reglas validadas

| Dataset | Reglas validadas | Reglas FAIL esperadas |
|---------|------------------|----------------------|
| D-PV-01 | R-INF-*, R-CO2-*, R-PW-*, R-EN-* | R-HVAC-EN-03, R-RH-02 (gaps conocidos) |
| D-PV-02 | R-OT-*, R-WX-*, R-EN-3, R-WD-* | R-OCC-01 si L-PV-06 sin resolver |
| D-PV-03 | R-AN-*, R-INF-* | R-FAULT-* (todas — bloqueado) |
| D-PV-04 | R-CO2-*, R-RH-1/3, R-N-* | R-RH-02 |
| D-PV-05 | todas high-confidence | gaps conocidos |
| D-PV-06 | R-HVAC-MODE, R-OT-* | diagnóstico mode-flapping |
| D-PV-07 | R-OCC-01 | R-OCC-01 si L-PV-06 |
| D-PV-08 | R-FAULT-02 + recovery | bloqueado |
| D-PV-09 | reglas físicas + métricas pipeline | none planned |
| D-PV-10 | reglas asociadas al experimento | dependiente |

## Mantenimiento de datasets

- Datasets persistentes (Caso B/C/D, baseline) regenerar cuando:
  - Cambia el seed default.
  - Se modifica una constante física observada.
  - Se cabla una avería (resolver L-PV-02).
- Hash sha256 de outputs persistentes se almacena en `tests/fixtures/dataset_hashes.json` (futuro).
- Los datasets no comprometen GitHub: solo se versionan los **scripts** que los generan, no los outputs binarios.
