# 00 — Investigación del generador (Fase 0)

## Contexto

Esta spec set valida la **plausibilidad física** del generador sintético BMS de CAPTIA-SYNTHETIC-DATA-BMS. Antes de proponer reglas, casos o validadores, este documento recoge los hallazgos de inspección directa del código (vendor + extensiones + servicio) y de las specs existentes (`docs/specs/synthetic-bms/`).

**Principio rector**: la implementación es la fuente de verdad. Donde la spec existente difiere del código, este documento registra ambas y la divergencia se traslada a `00-open-questions.md`.

## Alcance de la inspección

| Área | Rutas inspeccionadas |
|------|----------------------|
| Generador hexagonal | `vendor/synthetic-generator/src/synthetic_generator/{core,ports,domains,sinks}/` |
| Plug-in BMS | `vendor/synthetic-generator/src/synthetic_generator/domains/bms_classrooms/{plugin.py,physics/}` |
| Configuración de dominio | `vendor/synthetic-generator/config/domains/bms_classrooms/{domain.yaml,variables.yaml}` y `config/domains/bms_classrooms/{domain.yaml,variables.yaml,faults.yaml}` |
| Calibración BMS | `extensions/bms_calibration/src/bms_calibration/{faults.py,physics_overrides.py,school_calendar.py}` |
| Servicio FastAPI | `modules/bms-data-generator/src/bms_data_generator/{api/,services/}` |
| Specs existentes | `docs/specs/synthetic-bms/{01..10,STATUS}.md` y `00-*.md` |
| Schema canónico | `docs/CENTINELA_Guia_Alumnos_v4.md:141-180` |
| Observabilidad | `infra/{telegraf,prometheus,grafana,loki,promtail}/` y `compose/observability.yaml` |
| Tests | `vendor/.../tests/`, `extensions/bms_calibration/tests/`, `modules/.../tests/`, `tests/e2e/` |

## Hallazgos clave por área

### 1. Arquitectura del generador

- **Hexagonal**: `core/` agnóstico de dominio (runner, validator, anomalies, clock, rate). `ports/` define `DomainAdapterPort` y `SinkAdapterPort` como `Protocol`. `domains/` aloja plug-ins; `sinks/` aloja adapters de salida.
- **Único dominio en este build**: `bms_classrooms` (resto del catálogo CAPTIA-CONNECT no incluido — ver `vendor/synthetic-generator/PATCHES/001-bms-only.patch`).
- **Versión**: 0.1.0, snapshot upstream commit `2a793a55…` (2026-05-09) según `vendor/synthetic-generator/VENDOR.md:13-14`.

### 2. Modelos físicos implementados

13 modelos identificados con código concreto y parametrización vía dict de configuración:

| # | Función | Fichero | Líneas | Naturaleza |
|---|---------|---------|--------|------------|
| 1 | `simulate_indoor_temperature` | `physics/indoor.py` | 13-57 | Primer orden RC (tau=90 min default) con drift al exterior cuando HVAC off |
| 2 | `simulate_co2` | `physics/indoor.py` | 60-99 | Well-mixed, generación 7.5 ppm·min⁻¹·persona⁻¹, ventilación HVAC-dependiente |
| 3 | `simulate_humidity` | `physics/indoor.py` | 102-136 | Primer orden τ=180 min, target = outdoor_mean + 0.08·occupancy |
| 4 | `simulate_noise` | `physics/indoor.py` | 139-168 | Base + 0.35 dB(A)·persona |
| 5 | `simulate_illuminance` | `physics/indoor.py` | 171-203 | max(daylight, target) con target_on=550 lux, target_off=70 lux |
| 6 | `derive_pir_presence` | `physics/indoor.py` | 206-226 | Booleano con FP=0.4% y FN=1% |
| 7 | `derive_scene` | `physics/actuators.py` | 13-56 | {class, out_of_hours, manual} con override raro p=0.0008 |
| 8 | `thermostat_setpoint` | `physics/actuators.py` | 59-90 | 21°C class, 18°C out_of_hours, jitter N(0, 0.3°C) |
| 9 | `hvac_mode` | `physics/actuators.py` | 93-118 | {off, heat, cool, auto} por T_outdoor |
| 10 | `hvac_enable` | `physics/actuators.py` | 121-146 | Threshold-based: clase+occ → 0.4°C, cualquier escena → 1.5°C |
| 11 | `heating_valve_position` | `physics/actuators.py` | 149-169 | Proporcional `pos = clip(35·(setpoint-T), 0, 100)` solo si mode=heat |
| 12 | `light_state` | `physics/actuators.py` | 172-199 | Occ + daylight<250 lux, con extra aleatorio 12% |
| 13 | `simulate_power` + `integrate_energy_kwh` | `physics/energy.py` | 11-49 / 52-68 | Aditivo: 80W base + 180·light + 900·hvac + 8·occ + spikes raros; cumsum a kWh |

Modelos de contexto exterior:

| # | Función | Fichero | Líneas |
|---|---------|---------|--------|
| 14 | `outdoor_temperature` | `physics/environment.py` | 13-46 | Sinusoidal anual + EWMA noise (alpha=0.02) |
| 15 | `daylight_lux` | `physics/environment.py` | 49-79 | Día solar con longitud variable; pico ~700 lux |

Modelo de ocupación:

| # | Función | Fichero | Líneas |
|---|---------|---------|--------|
| 16 | `generate_occupancy_count` | `physics/occupancy.py` | 39-81 | Poisson(capacity·util·p_occ·day_mult), clipped a capacity |

### 3. Calendario y horarios

- Calendario lectivo: configurable por mes inicio/fin + holidays + slots horarios (`config/domains/bms_classrooms/domain.yaml:6-31`).
- Override vendor → BMS: el repo añade fechas reales (Navidad 2025, Reyes, San José, Pascua) en `config/domains/bms_classrooms/domain.yaml:9-17`.
- Calendario BMS dedicado: `extensions/bms_calibration/src/bms_calibration/school_calendar.py:15-40` — `ValenciaSchoolCalendar` con 4 períodos vacacionales 2025-26 (Navidad, Fallas, Pascua, Verano).
- **Discrepancia**: hay **dos** fuentes de verdad para el calendario (vendor `domain.yaml` y `school_calendar.py`). En el path de generación activo se usa el del vendor; `ValenciaSchoolCalendar` está disponible pero **no se invoca** en `runner_service`.

### 4. Meteo

- Sintético puramente determinista (`environment.py:13-46`). No hay fixtures de meteo real ni acoplamiento con ERA5 (L-10 en `synthetic-bms/00-open-questions.md` confirmado: ERA5 fuera de v1).
- Variables exteriores generadas: `outdoor_temp`, `daylight_lux`. **NO existen** `solar_irradiance`, `wind_speed`, `humidity_outdoor` aunque la spec `02-domain-spec.md:72-73` los lista.

### 5. Ocupación

- Por aula: `capacity ~ N(28, 6)`, `util ~ N(0.75, 0.10)` clipped (`occupancy.py:13-36`).
- Por día: `day_mult ~ N(1.0, 0.12)` clipped a [0.6, 1.4].
- Por timestamp: `expected = capacity·util·p_occ·day_mult`; `actual ~ Poisson(expected)` clipped a [0, capacity].
- `p_occ` viene de los slots horarios (default 08:00-15:00 → 0.85; 15:00-20:00 → 0.30 en BMS override).

### 6. Determinismo

- `np.random.default_rng(seed)` consistente (verificado en `runner.py`, `plugin.py`, `faults.py:51`).
- Default `seed=42` (ADR-008).
- **Sin uso de `np.random.seed()`** (estado global) — verificado por inspección.
- Tests snapshot en `vendor/.../tests/integration/test_determinism.py` y `extensions/bms_calibration/tests/test_determinism.py` (hash sha256 esperado).

### 7. Anomalías de dato (vendor)

Tres tipos en `core/anomalies.py:12-110`:

- `p_missing` (per-point): elimina punto del stream.
- `p_outlier` (per-point): perturba con `value += N(0, 3·|value|)` y marca `quality=OUTLIER`.
- `burst_missing_prob_per_day` con `burst_duration_range`: gaps multi-punto.

**No implementados** aunque el modelo lo permitiría:
- Stuck sensor (valor constante).
- Drift gradual (offset creciente).
- Offset fijo.
- Duplicados.
- Out-of-order.
- Latencia/jitter.
- Datos definidos en `core/config.py` (`PerturbationsConfig`) pero **no aplicados en el runner**: `jitter_ms`, `duplicate_probability`, `out_of_order_probability`, `gap_probability`. Ver `00-open-questions.md`.

### 8. Averías físicas (extensions BMS)

`extensions/bms_calibration/src/bms_calibration/faults.py:23-78` define 4 tipos (ADR-010):

- `sensor_drift` (24 h por episodio, severity ∈ [0.3, 1.0]).
- `valve_stuck` (1 h por episodio).
- `fan_failure` (4 h por episodio).
- `refrigerant_low` (12 h por episodio).

`FaultInjector.inject()` genera `FaultEvent` con `(start, end, severity)` por activo.

**Crítico**: los `FaultEvent` se generan pero **no se materializan** automáticamente en señales (no hay sink que los traduzca a `state_events` con `variable=fault.<tipo>` como pide `02-domain-spec.md:144-152`). El path de generación principal (`RunnerService._build_runner` en `runner_service.py:59-105`) **no invoca** `FaultInjector`.

### 9. Sinks

- `MQTTSinkAdapter` (`sinks/mqtt.py`): payload `{"value": float, "ts_ns": int}`, topic `captia/{env}/{tenant}/{site}/{device}/telemetry/{variable}`. Booleanos a 1.0/0.0.
- `FileSinkAdapter` (`sinks/file.py`): formatos `csv_long`, `csv_wide`, `jsonl`. Para dump tipo Caso B se fuerza `format=csv_long` (mal nombrado en CLI; el dump-service lo escribe como `.lp` line-protocol cuando se le pide — ver `dump_service.py:152-153`).
- `StdoutSinkAdapter`, `CompositeSink`, `NullSink`.
- **Sin** `LineProtocolSinkAdapter` propio: la salida `.lp` se obtiene reformateando `csv_long` o vía herramientas externas.

### 10. Configuración

- `ScenarioConfig` (Pydantic) en `core/config.py`. Campos top-level: `project`, `simulation`, `domain`, `phases`, `perturbations`, `anomalies`, `sinks`, `output`.
- 4 escenarios proyecto en `config/projects/`: `bms_v1_demo.yaml` (Caso A), `bms_v1_caseB_consumption.yaml`, `bms_v1_caseC_faults.yaml`, `bms_v1_caseD_iaq.yaml`.
- **Discrepancia parámetros físicos**: las claves `co2.base_ppm`, `co2.per_person_ppm`, `co2.decay_rate` en `domain.yaml:38-41` y `vendor/.../domain.yaml:38-41` **no son leídas** por `simulate_co2` (que lee `outdoor_ppm`, `gen_ppm_per_min_per_person`, `vent_k_per_min`, `leak_k_per_min`). Lo mismo para `indoor.thermal_mass`, `indoor.heating_power`, `indoor.cooling_effect` (no usados en `simulate_indoor_temperature`). Ver `00-open-questions.md` L-PV-08.

### 11. Tests

- Vendor: 80 unit + 40 integration + ~20 snapshot + 5 performance. Markers `unit`, `integration`, `snapshot`, `performance` (`pyproject.toml`).
- Extensions BMS: `test_faults.py` (determinismo), `test_physics_overrides.py`, `test_school_calendar.py`, `test_determinism.py` (snapshot hash).
- Servicio: `test_config.py`, `test_metrics.py`, `test_runner_service.py`, `test_dump_service.py`, `test_api_health.py`, `test_api_control.py`, `test_api_datasets.py`.
- E2E: `tests/e2e/{test_pipeline_iot,test_dump_caseB,test_faults_caseC,test_iaq_caseD}.py` (markers `smoke + slow`).
- **No existen tests de plausibilidad física**: ni rate-of-change, ni monotonicidad de contadores, ni conservación, ni causalidad cruzada (occupancy → CO₂ slope), ni firmas de avería.

### 12. Validación pre-emisión

`core/validator.py:22-89` define `ContractValidator` con checks de:
- `timestamp` no nulo (línea 43).
- `asset_id` mayúsculas (46).
- `variable` minúsculas (49).
- Rango duro vía `expected_range_hard` del inventario (57-71).

**No se enforce en el path BMS**: `runner_service._build_runner` no instancia `ContractValidator` y la salida va directamente a sinks. Únicamente los sinks aplican clamping (`np.clip` en `indoor.py`, `energy.py`).

### 13. Catálogo de variables real (vendor)

`vendor/synthetic-generator/config/domains/bms_classrooms/variables.yaml:24-202` define 21 variables del activo `classroom`:

- **Sensors environmental** (6): `temperature`, `humidity`, `co2`, `iaq_index`, `noise`, `illuminance`.
- **Sensors occupancy** (2): `occupancy` (integer), `presence_pir` (boolean).
- **Sensors external** (2): `outdoor_temp`, `daylight_lux`.
- **Actuators HVAC** (4): `thermostat_setpoint`, `hvac_mode`, `hvac_enable`, `heating_valve_pos`.
- **Actuators control** (5): `scene_mode`, `relay_1..relay_4`.
- **Sensors energy** (2): `power`, `energy`.

**Discrepancia con `synthetic-bms/02-domain-spec.md:60-85`**: la spec lista nombres como `temperature_01`, `relative_humidity_01`, `power_01`, `temperature_supply`, `temperature_return`, `solar_irradiance`, `temperature_outdoor`, `ac_state`, `ac_control`, `fan_speed_01..03_state`, `light_01_state..02_state`, `valve_control`, `valve_state`, `people_count`. Estas variables **no existen** en el vendor; los nombres reales están sin sufijo `_NN` y son los listados arriba. Ver `00-open-questions.md` L-PV-01.

### 14. Servicio FastAPI

- `RunnerService` (`runner_service.py:111-238`) y `DumpService` orquestan al vendor con job state machine, single active job, threading.
- Métricas Prometheus `captia_bms_*` (`metrics.py`): 8 contadores y gauges.
- `calibration_loader.py:13-26` define `load_faults_config` y `load_physics_overrides` pero **no son invocados** desde `runner_service` ni `dump_service` (dead-end actual; gap conocido).

## Aspectos no investigados (delegados)

- Performance real del generador (≥700 pts/aula·h declarados en AC-03 pero sin benchmark formal — confirmado por `synthetic-bms/STATUS.md`).
- Comportamiento del vendor en `live` phase con `lookahead_hours` y `regenerate_on_exhaustion` (código presente pero no inspeccionado en detalle).
- Carga real de Mosquitto bajo Caso A 70 aulas (tuning a 200k mensajes en queue confirmado en `infra/mosquitto/mosquitto.conf:32-36` pero sin medición).

## Conclusión

El generador implementa un **modelo físico parametrizable y determinista** con cobertura honesta de las dinámicas BMS clave (térmica, CO₂, energía, ocupación). La capa BMS añade calendario y averías. Los hooks de calibración están listos pero sin datos reales (L-01).

Las **discrepancias críticas** detectadas (variables `temperature_01` vs `temperature`; claves `co2.per_person_ppm` ignoradas; calibration_loader sin wiring; faults sin sink a `state_events`) son los principales bloqueadores para una validación física robusta y se documentan en `00-open-questions.md`.

El siguiente paso (`01-observed-physical-model.md`) describe modelo a modelo lo que el código realmente hace.
