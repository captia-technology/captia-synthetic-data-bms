# 00 — Lagunas y preguntas abiertas (Fase 0)

## Contexto

Inventario de ambigüedades, divergencias y deudas técnicas detectadas durante la inspección. Cada laguna tiene impacto explícito sobre la validación física y, donde aplica, una propuesta de resolución que se desarrolla en specs posteriores.

**Convención de IDs**: `L-PV-NN` (lagunas de Physics Validation), separadas de las `L-NN` ya existentes en `docs/specs/synthetic-bms/00-open-questions.md`. Cuando una laguna se solape con una `L-NN`, se referencia explícitamente.

## Lagunas críticas (bloquean validación robusta)

### L-PV-01 — Catálogo de variables vendor ↔ producción divergente [BLOCKER]

- **Hallazgo (actualizado tras revisar PPTX)**: `vendor/synthetic-generator/config/domains/bms_classrooms/variables.yaml:24-202` define 21 variables con nombres `temperature`, `humidity`, `co2`, `power`, `energy`, `presence_pir`, `outdoor_temp`, `daylight_lux`, `thermostat_setpoint`, `hvac_mode`, `hvac_enable`, `heating_valve_pos`, `scene_mode`, `relay_1..relay_4`, `iaq_index`, `noise`, `illuminance`, `occupancy`.
  
  La **producción real en `simarro-prod`** (ground truth `docs/influxdb-simarro-buckets.pptx` slide 14, snapshot 2026-03-28) usa nombres **completamente distintos**: `temperature_01`, `temperature_01_sp`, `temperature-indoor`, `relative-humidity`, `t-voc`, `iaq-index`, `avg-sound-level`, `max-sound-level`, `luminosity`, `occupancy` (bool), `people-count`, `power_01`, `ac_state`, `ac_control`, `aire`, `aire_state`, `fan_speed_01..03` + `_state`, `light_01..02` + `_state`, `valve_control`, `valve_state`.

  La spec `docs/specs/synthetic-bms/02-domain-spec.md:60-85` parcialmente alinea con producción (usa `temperature_01`, `power_01`, etc.) pero también lista variables que **no existen ni en vendor ni en producción** (`temperature_supply`, `temperature_return`, `solar_irradiance`).
- **Impacto severo**: el generador sintético **NO es drop-in replacement** de telemetría real. Cualquier dashboard, alerta, query Flux, modelo ML entrenado contra producción **no funciona** contra datos sintéticos.
- **Propuesta**:
  - Crear nueva spec `11-production-signal-mapping.md` con tabla canónica vendor → producción (entregada).
  - Implementar override de `config/domains/bms_classrooms/variables.yaml` con nombres alineados a producción + AliasSink wrapper (T-PV-21..23 en `10-*`).
  - Rectificar `synthetic-bms/02-domain-spec.md` eliminando `temperature_supply`, `temperature_return`, `solar_irradiance`, `t_voc` (con underscore — el real es `t-voc`).
- **Confidence**: alto.
- **Severity**: **BLOCKER** (elevado de "blocker para reglas" a "blocker estructural para todo el caso de uso").

### L-PV-02 — Avería física no se materializa en `state_events`

- **Hallazgo**: `extensions/bms_calibration/src/bms_calibration/faults.py:39-78` define `FaultInjector.inject()` que produce `FaultEvent(fault_type, asset_id, start, end, severity)` deterministas. **Ningún sink ni servicio** del path `RunnerService._build_runner` (`runner_service.py:59-105`) consume estos eventos. La promesa de `synthetic-bms/02-domain-spec.md:144-152` (`captia_point` con `variable=fault.<tipo>` en bucket `state_events`) **no está implementada**.
- **Impacto**: imposible distinguir avería física de anomalía de dato sin trazabilidad de origen. Caso C (Caso de uso "fault detection") queda sin etiquetas verdaderas en datos sintéticos.
- **Propuesta**:
  - Spec `07-validator-design.md` propone un `FaultEventSink` que mapee `FaultEvent` → `DataPoint(variable=fault.<tipo>, value=1.0|0.0)` y emita a `state_events`.
  - Spec `04-physical-plausibility-rules.md` define `fault_signature` como regla que requiere comparar la marca esperada con la salida real.
  - Spec `10-implementation-readiness.md` clasifica este wiring como "implementar ya" (cambio mecánico, no requiere ground-truth).
- **Confidence**: alto.
- **Severity**: blocker para Caso C real.

### L-PV-03 — Parámetros físicos de `domain.yaml` ignorados

- **Hallazgo**: `config/domains/bms_classrooms/domain.yaml:38-49` define claves físicas (`co2.base_ppm`, `co2.per_person_ppm=18.5`, `co2.decay_rate=0.03`, `indoor.thermal_mass`, `indoor.heating_power`, `indoor.cooling_effect`, `humidity.base_rh`, `humidity.outdoor_influence`, `noise.base_db`, `noise.per_person_db`, `light.artificial_lux`, `light.daylight_factor`). El código de `physics/indoor.py:81-84` lee otras llaves: `outdoor_ppm`, `gen_ppm_per_min_per_person` (=7.5 default), `vent_k_per_min`, `leak_k_per_min`. Las llaves de `domain.yaml` no aparecen en ningún `cfg.get(...)` del código.
- **Impacto**: la calibración manual desde YAML no funciona. Los valores de `02-domain-spec.md:122-126` (4.5 ppm/persona/min ASHRAE) **no se aplican** al runtime. El generador produce con defaults hardcoded (7.5 ppm/persona/min) que ni siquiera coinciden con el valor citado en `02-domain-spec.md`.
- **Propuesta**:
  - Spec `01-observed-physical-model.md` documenta los **defaults reales** (7.5 ppm/persona/min, no 4.5).
  - Spec `04-physical-plausibility-rules.md` evalúa coherencia respecto al valor literatura (4.5) y flag-ea la divergencia generada.
  - Spec `10-implementation-readiness.md` propone unificar nombres de claves físicas entre `domain.yaml` y `physics/*.py` (cambio en vendor → vía `PATCHES/`).
- **Confidence**: alto (ambos ficheros inspeccionados).
- **Severity**: medio para validación, alto para calibración real (L-01 del set padre).

### L-PV-04 — `calibration_loader` sin caller

- **Hallazgo**: `modules/bms-data-generator/src/bms_data_generator/services/calibration_loader.py:13-26` define `load_faults_config()` y `load_physics_overrides()`. Búsqueda en `runner_service.py` y `dump_service.py`: **ningún import** de `calibration_loader`.
- **Impacto**: ni overrides de calibración ni configuración de faults llegan al `ScenarioRunner` desde la API. El path API → vendor está incompleto.
- **Propuesta**: spec `07-validator-design.md` propone wiring en `RunnerService._build_runner` (cargar faults config y, si `BMS_FAULTS_ENABLED=true`, inyectar `FaultInjector` antes de sinks).
- **Confidence**: alto.
- **Severity**: medio (gap de funcionalidad, no bloquea validación si se documenta).

### L-PV-05 — `ContractValidator` definido pero no enforced

- **Hallazgo**: `vendor/synthetic-generator/src/synthetic_generator/core/validator.py:22-89` provee validación contractual pre-emisión (timestamp, case conventions, `expected_range_hard` desde inventario). **No se instancia** en el path BMS (no hay `ContractValidator(...)` en `runner_service.py`, `dump_service.py`, o en `vendor/.../core/runner.py` por defecto).
- **Impacto**: salidas pueden violar `expected_range_hard` sin detección — los `np.clip(...)` actuales en `indoor.py:97` (CO₂ a 2200), `indoor.py:136` (humidity a [10, 90]) y `energy.py:49` (power a [0, 6000]) son **clipping silencioso** que esconde problemas.
- **Propuesta**: spec `07-validator-design.md` propone un wrapper de sink que instancie `ContractValidator(inventory=...)` y aplique `validate(...)` antes de emitir, surfacing violaciones a métricas Prometheus (en lugar de clipping silencioso).
- **Confidence**: alto.
- **Severity**: medio.

### L-PV-06 — Calendario duplicado y no unificado

- **Hallazgo**: hay dos fuentes de calendario:
  - `vendor/.../config/domains/bms_classrooms/domain.yaml:6-12` (`school_start_month`, `school_end_month`, lista de `holidays`).
  - `extensions/bms_calibration/src/bms_calibration/school_calendar.py:22-27` (`ValenciaSchoolCalendar` con 4 períodos vacacionales 2025-26 reales).
- En el path activo se usa el del vendor; el de extensions **nunca se invoca** en runtime.
- **Impacto**: período vacacional real (Navidad 2025-12-22 → 2026-01-07; Fallas; Pascua; Verano) se simula con calendario aproximado del vendor. Ocupación durante festivos puede no coincidir con realidad.
- **Propuesta**:
  - Spec `07-validator-design.md` propone que la validación use `ValenciaSchoolCalendar` como referencia para reglas de tipo "ocupación = 0 durante vacaciones".
  - `10-implementation-readiness.md`: opción A — wire `ValenciaSchoolCalendar` en el path de generación; opción B — sincronizar `domain.yaml` con las fechas oficiales.
- **Confidence**: alto.
- **Severity**: bajo a medio.

## Lagunas en el modelo físico

### L-PV-07 — HVAC sin anti short-cycle

- **Hallazgo**: `physics/actuators.py:121-146` decide enable por umbral instantáneo (sin tiempo mínimo on/off). `core/control_utils.py:40-66` ofrece `MinOnOffTimer` pero no se usa en BMS physics.
- **Impacto**: en condiciones límite (T_indoor oscilando alrededor de setpoint), `hvac_enable` puede toggling rápidamente. En realidad el HVAC tiene timer mínimo (típicamente 5-10 min on/off).
- **Propuesta**:
  - Regla `04-physical-plausibility-rules.md` `state_consistency` que detecte ciclos < 5 min como indicador de ausencia de anti short-cycle.
  - `10-implementation-readiness.md` propone integrar `MinOnOffTimer` en una próxima iteración del vendor.
- **Confidence**: alto.
- **Severity**: medio (degrada realismo en escenarios marginales).

### L-PV-08 — Modelo HVAC sin acción frigorífica explícita

- **Hallazgo**: `simulate_indoor_temperature` (`physics/indoor.py:13-57`) modela calefacción como movimiento al setpoint cuando HVAC enabled, pero **no diferencia** modo `cool` vs `heat`. La `heating_valve_position` solo aplica si `mode==heat`. **No existe** `cooling_valve_position` ni curva de capacidad frigorífica vs T_outdoor. La temperatura siempre tiende al setpoint sin coste energético diferenciado por modo.
- **Impacto**: en verano (T_out > 26 → mode=cool), la temperatura interior baja por el mismo mecanismo de RC con target=setpoint. No hay degradación de capacidad por T_out alta, ni ciclo cooling que revele compresor activo. La power model añade `900W·hvac_enable` independiente del modo.
- **Propuesta**:
  - `01-observed-physical-model.md` documenta esta limitación.
  - `04-physical-plausibility-rules.md` regla `causal_lag` espera diferentes `time_to_setpoint` heat vs cool (actualmente serían iguales — flag).
  - `10-implementation-readiness.md` propone curva de capacidad cooling como mejora del vendor.
- **Confidence**: alto.
- **Severity**: medio.

### L-PV-09 — Modelo de humedad ignora carga latente HVAC

- **Hallazgo**: `simulate_humidity` (`physics/indoor.py:102-136`) usa target `outdoor_mean + 0.08·occupancy`; **no depende** de `hvac_enable` ni de modo cooling (que en realidad deshumidifica fuertemente).
- **Impacto**: en verano con HVAC cooling activo, la humedad real bajaría 10-20 puntos %RH; el modelo no lo refleja.
- **Propuesta**:
  - `01-observed-physical-model.md` documenta la limitación.
  - `04-physical-plausibility-rules.md` regla `anti_correlation` espera RH ↓ cuando `hvac_mode=cool & hvac_enable=1` (validar que **no** se cumple en datos actuales).
  - `10-implementation-readiness.md` propone añadir término `-cool_dehumid·(hvac_enable & cool)` al target.
- **Confidence**: alto.
- **Severity**: medio.

### L-PV-10 — Realimentación HVAC ↔ T_indoor con 1 paso de retraso

- **Hallazgo**: orden de cómputo: `simulate_indoor_temperature` lee `hvac_enable[i]` (línea `physics/indoor.py:51`) pero `hvac_enable` se calcula **después** desde `temperature` (línea `physics/actuators.py:121-146`). Examinando con más detalle: el plug-in computa todo en un bucle por aula, pasando arrays pre-calculados — significa que `hvac_enable` en `simulate_indoor_temperature` viene de un cálculo previo (probablemente con T_indoor de step anterior).
- **Impacto**: lag implícito de 1 sample entre cambio T y respuesta HVAC. A 5 s de frecuencia es despreciable; a 5 min puede afectar transiciones rápidas.
- **Propuesta**: spec `01-observed-physical-model.md` documenta la realimentación lazy y su escala temporal. Regla `causal_lag` valida que la respuesta no sea instantánea.
- **Confidence**: medio (requiere lectura de `plugin.py` para confirmar el flow exacto).
- **Severity**: bajo.

### L-PV-11 — `simulate_co2` permite que CO₂ no baje hasta `outdoor_ppm`

- **Hallazgo**: `physics/indoor.py:97` clip a `[outdoor_ppm, 2200]`. El término de leak `leak_k=0.01/min` es bajo (τ = 100 min); en una habitación cerrada toda la noche el CO₂ debería caer prácticamente al exterior, pero con leak tan bajo y `vent_k=0` cuando HVAC off, la decadencia es lenta.
- **Impacto**: una sala vacía y con HVAC off durante 6 h debería ver CO₂ → 420 ppm; con `leak_k=0.01` y τ ≈ 100 min, en 6 h llegará a `420 + (CO2_initial - 420)·exp(-360/100) ≈ 420 + 30·exp(-3.6) ≈ 421 ppm` si C_initial = 1500. Acceptable.
- **Propuesta**: validar con regla `bounded_response` que el CO₂ post-noche cae a < 500 ppm en aulas con ocupación nula >6h. Documentar como caso de validación en `03-physical-cases.md`.
- **Confidence**: alto.
- **Severity**: bajo.

## Lagunas en el contexto exterior

### L-PV-12 — Sin meteo real

- **Hallazgo**: `physics/environment.py:13-79` genera meteo sintética (sinusoidal anual + EWMA noise). No se consume API ni fixtures de meteo real.
- **Impacto**: validar con eventos meteorológicos reales (tormentas, olas de calor) requiere fixtures externas que no existen.
- **Propuesta**: spec `06-validation-datasets.md` propone fixtures meteo sintéticas marcadas (e.g., "ola de calor" = T_out forzada a 38°C 5 días). Para v2, evaluar consumo de ERA5 (referido en `synthetic-bms/00-open-questions.md` L-10).
- **Severity**: bajo (la validación física puede ser interna sin meteo real).

### L-PV-13 — `daylight_lux` peak fijo a 700 lux indoor

- **Hallazgo**: `physics/environment.py:77` peak hardcoded a 700 lux ("indoor daylight near windows"). No varía por aula (orientación), ni por estación (cobertura nubosa), ni por persianas.
- **Impacto**: todas las aulas tienen idéntico patrón de daylight, lo cual es irreal (orientación N vs S → 200 vs 1500 lux peak).
- **Propuesta**: documentar en `01-observed-physical-model.md`. Propuesta v2: factor por orientación de aula.
- **Severity**: bajo.

## Lagunas en anomalías y averías

### L-PV-14 — `PerturbationsConfig` definido pero sin aplicación

- **Hallazgo**: `vendor/.../core/config.py` define `jitter_ms`, `duplicate_probability`, `out_of_order_probability`, `gap_probability`. Inspección de `core/runner.py`: ningún caller. Solo `AnomalyEngine` se aplica.
- **Impacto**: no se pueden validar pipelines downstream contra perturbaciones de transporte (jitter, duplicados, orden). Robustez ingest no testada.
- **Propuesta**: spec `04-physical-plausibility-rules.md` separa `anomaly_signature` (data-level, lo que ya hay) de `transport_signature` (perturbaciones — pendiente). `10-implementation-readiness.md` propone activar `PerturbationEngine` análogo a `AnomalyEngine` en una iteración futura.
- **Severity**: medio para tests E2E robustez.

### L-PV-15 — Anomalías limitadas (solo missing/outlier/burst)

- **Hallazgo**: `core/anomalies.py:12-18` solo soporta missing, outlier, burst missing. **No hay**:
  - Stuck sensor (valor constante).
  - Drift gradual (offset creciente).
  - Offset fijo.
  - Patología cross-variable (e.g., 2 sensores muestran lectura idéntica).
- **Impacto**: cobertura limitada de patología real de telemetría IoT.
- **Propuesta**: spec `03-physical-cases.md` familia 7 ("anomalías de dato") enumera todas las que **deberían** existir; `10-implementation-readiness.md` clasifica cuáles son fáciles de añadir y cuáles requieren cambios estructurales en el `AnomalyEngine`.
- **Severity**: medio.

## Lagunas en wiring y observabilidad

### L-PV-16 — Sin métricas Prometheus de plausibilidad física

- **Hallazgo**: `modules/bms-data-generator/src/bms_data_generator/metrics.py` define `captia_bms_*` (counters de mensajes, errores, points generados, faults inyectados, dump duration). **No hay** métricas de coherencia física (energy balance, HVAC lag, CO₂ coupling, fault signature).
- **Impacto**: imposible alertar sobre "el generador está produciendo datos físicamente implausibles" desde Prometheus.
- **Propuesta**: spec `09-physical-observability.md` define 8-12 métricas `captia_physics_*` con prefijo separado.
- **Severity**: medio.

### L-PV-17 — Sin Flux task de validación física en buckets

- **Hallazgo**: `infra/influxdb/init/init_buckets_tasks.sh` provisiona 5 tareas Flux de downsampling (analog_1m, state_1m, presence_1m, counter_1m, _15m, _1h) pero **ninguna** de cómputo derivado de validación (e.g., "CO₂ rate vs occupancy slope hourly").
- **Impacto**: cualquier métrica de validación calculada en Influx debe correr ad-hoc desde Grafana o desde el generator (latencia y carga).
- **Propuesta**: spec `09-physical-observability.md` propone `physics_validation_hourly.flux` que escribe a nuevo bucket `physics_metrics`.
- **Severity**: medio.

## Lagunas detectadas en revisión PPTX (canonical signal mapping)

### L-PV-18 — Bucket `telemetry_events` faltante

- **Hallazgo**: `docs/influxdb-simarro-buckets.pptx` slide 8 documenta el **7º bucket operativo** en producción:
  - `telemetry_events` (90d retention)
  - measurement: `captia_cmd_event`
  - tags: 5 canónicos + `event_type ∈ {cmd_authorized, cmd_rejected, sniper_error}`
  - 7 fields string: `cmd_id, metric, target, reason, error, source, detail`
  - producer: Telegraf output #3 + 2º mqtt_consumer con topics `captia/+/+/+/+/event/+`, `captia/sniper/event`
- **Estado actual local**:
  - `infra/influxdb/init/init_buckets_tasks.sh:62-67` solo crea 6 buckets (falta `telemetry_events`).
  - `infra/telegraf/telegraf.conf:35-50` solo tiene 1 `mqtt_consumer` (telemetry).
- **Impacto**: el generador sintético no puede emitir auditoría de comandos ni eventos de plataforma. Caso C (faults) no puede usar este canal canónico — actualmente el spec set propone marcar faults en `state_events` con `variable=fault.<tipo>`, lo cual es válido pero distinto del patrón producción.
- **Propuesta**:
  - Añadir línea en `init_buckets_tasks.sh:67` → `create_bucket_if_missing "telemetry_events" "90d"`.
  - Añadir 2º `mqtt_consumer` en `telegraf.conf` con `name_override = "captia_cmd_event"` y output #3 al bucket `telemetry_events`.
  - Documentar measurement `captia_cmd_event` (distinto de `captia_point`) en `09-physical-observability.md`.
  - **Para FaultEvents**: decidir si materializar como `captia_point` en `state_events` (mi propuesta inicial) o como `captia_cmd_event` en `telemetry_events` con `event_type=fault_<tipo>` (más alineado con producción).
- **Severity**: **High** (gap estructural de pipeline producción).
- **Confidence**: alto.

### L-PV-19 — Measurement `state_events` divergente con producción

- **Hallazgo**: `docs/influxdb-simarro-buckets.pptx` slide 8 dice **explícitamente**:
  > Measurement: `captia_point` (NO captia_point_state)
  
  Pero `infra/telegraf/telegraf.conf:101` hace:
  ```toml
  [[processors.clone]]
    namepass = ["captia_point"]
    name_override = "captia_point_state"   # ← divergente con producción
  ```
- **Implicación**: en producción, `state_events` y `telemetry` usan el **mismo measurement** (`captia_point`); solo difieren en bucket. Las queries Flux son más simples (un solo `from(bucket:"state_events").filter(_measurement=="captia_point")`).
  
  En nuestro stack local, las queries deben filtrar por measurement distinto si quieren acceder a `state_events`.
- **Impacto**: query inconsistency. Dashboards y alertas de producción no funcionan en local sin reescribir.
- **Propuesta**: eliminar `name_override = "captia_point_state"` en `telegraf.conf:101`. Dejar que el clone preserve el measurement original `captia_point`. La diferenciación sigue funcionando porque van a buckets distintos (`telemetry` vs `state_events`).
- **Severity**: **Medium** (compatibilidad query path).
- **Confidence**: alto.

### L-PV-20 — Streams MQTT canónicos no implementados

- **Hallazgo**: `docs/captia-connect-partner-integration.pptx` slide 5 define **5 valores canónicos** del segmento `stream` del topic 7-segment:
  - `telemetry` — sensor readings (✓ implementado)
  - `cmd` — comandos del adapter (NO implementado)
  - `ack` — ack del device (NO implementado)
  - `state` — device state updates (NO implementado — podría ser overlap con bucket state_events)
  - `event` — platform events (NO implementado — bloqueado por L-PV-18)
- **Impacto**: el generador sintético solo simula la dirección **inbound** (device → broker). No puede simular escenarios de comandos remotos, ack timing, o eventos de plataforma. Limita Caso C realista (averías deberían producir `event` con `event_type=fault_*`).
- **Propuesta**:
  - Caso A live: opcional añadir un mock de comandos (`cmd` topics) que el generador pueda recibir y respondiera con `ack`. Fuera de v1.
  - Caso C faults: emitir `event` con `event_type=fault_<tipo>` cuando se cablee L-PV-02.
- **Severity**: **Medium** (afecta cobertura de pipeline producción).
- **Confidence**: alto.

### L-PV-21 — `captia_metadata` bucket vacío

- **Hallazgo**: `docs/influxdb-simarro-buckets.pptx` slide 9 documenta que `captia_metadata` (retention infinita) contiene **3 measurements**:
  - `captia_point_meta` (catálogo de variables, **21 fields**: metric_kind, storage_mode, data_type, unit, range_min, range_max, display_name, is_actuator, _deleted tombstone, ...)
  - `captia_domain_meta` (config dominio, 10 fields)
  - `captia_device_registry` (devices físicos)
  
  Es el **SSOT** del catálogo, leído por las 6 Flux tasks (allowlists), el adapter y las UIs de configuración.
- **Estado actual**: `infra/influxdb/init/init_buckets_tasks.sh:67` crea el bucket pero **vacío**. No hay `metadata-bootstrap` que lo pueble.
- **Impacto**:
  - Las Flux tasks de downsampling **terminan en success sin escribir nada** (per slide 12: "si captia_metadata está vacío (post-wipe), las tasks tier-1 terminan en success sin escribir nada. NO genera error").
  - Es decir: nuestros downsamples de `telemetry → telemetry_1m`, `_15m`, `_1h` **probablemente no escriben datos**.
  - El adapter no puede listar variables disponibles para dashboards.
- **Propuesta**:
  - Añadir script `infra/influxdb/init/bootstrap_metadata.sh` (o extender `init_buckets_tasks.sh`) que poblé `captia_point_meta` desde `config/domains/bms_classrooms/variables.yaml` (alineado con producción tras T-PV-21).
  - Definir tags y fields exactos según slide 9 (`captia_env`, `domain_id`, `site_id`, `asset_id`, `asset_type`, `variable` + 21 fields).
- **Severity**: **High** (rollups no funcionan sin esto).
- **Confidence**: alto.

### L-PV-22 — Convención routing on-change incompleta

- **Hallazgo**: `docs/captia-connect-partner-integration.pptx` slide 7 dice que el routing on-change es por **suffix glob**:
  ```
  *_cmd  *_ack  *_status  *_state  *_st  *_active
  *_enable  *_in_progress  relay_*  *_setpoint  *_sp  *_mode
  ```
  
  Pero slide 8 dice que también se decide por **`metric_kind`** (`bool_state`, `setpoint_step` → on_change).
  
  Variables como `ac_control` (setpoint_step) **NO matchean ningún glob** de los listados. Producción debe decidir por catálogo.
- **Impacto**: si el routing en nuestro Telegraf solo usa glob (`infra/telegraf/telegraf.conf:103-117`), variables como `ac_control` se enrutan **incorrectamente** a `telemetry` cuando deberían ir a `state_events`.
- **Propuesta**:
  - Añadir tagpass específico para `ac_control`, `valve_control`, `aire`, etc. (si vamos a producir esos nombres tras T-PV-21).
  - O: implementar un processor más inteligente que consulte `captia_metadata` para decidir routing (más complejo, pero alineado con producción).
- **Severity**: **Medium**.
- **Confidence**: medium (la convención exacta no está al 100% clara — los PPTX se contradicen levemente entre slide 7 y slide 8).

### L-PV-23 — `OUTDOOR` asset y meteo separada

- **Hallazgo**: producción tiene `outdoor_temp` (vendor) emitido por **cada aula** (heredado de generación per-asset), pero en producción real `temperature-outdoor` (kebab) viene de un asset separado tipo `OUTDOOR` o estación meteo. Ver `02-domain-spec.md:72-73` que lista `temperature_outdoor` y `solar_irradiance` como "continua (sitio)" — sugiere asset separado.
- **Impacto**: cardinality InfluxDB inflada (10 aulas × N_meteo_vars vs 1 OUTDOOR × N_meteo_vars). Coupling artificial entre meteo y aula.
- **Propuesta**:
  - Crear asset_id sintético `OUTDOOR` que emite `temperature-outdoor`, `daylight-lux` (kebab), opcional `solar_irradiance` (sin modelo aún).
  - Las aulas **no** emiten outdoor_temp; consumen del asset OUTDOOR via Influx en queries downstream.
  - Eliminar `outdoor_temp` del catálogo per-aula tras T-PV-21.
- **Severity**: **Medium** (afecta cardinality y semántica producción).
- **Confidence**: medium (no confirmado al 100% qué asset emite meteo en producción real).

## Lagunas heredadas (de `synthetic-bms/00-open-questions.md`)

| Hereda | Estado | Tratamiento en este spec set |
|--------|--------|------------------------------|
| L-01 (calibración real) | Pendiente post-v1 | Decisión usuario: plausibilidad ahora con literatura, ground-truth marcado por regla. Ver `04-*` y `08-*`. |
| L-04 (infra Simarro) | Post-v1 | No bloquea validación interna. |
| L-10 (ERA5) | Fuera v1 | Confirmamos en L-PV-12. |
| L-11 (anonimización dump real) | No aplica | Sintético puro v1. |

## Resumen — prioridad para `10-implementation-readiness.md`

| ID | Severity | Implementable ya | Bloquea validación crítica |
|----|----------|------------------|---------------------------|
| L-PV-01 | **BLOCKER** (drop-in replacement) | Sí (override variables.yaml + AliasSink) | **Sí** |
| L-PV-02 | blocker (Caso C real) | Sí (FaultEventSink) | Sí |
| L-PV-03 | medio | Sí (cambio en vendor PATCH o renombrado) | Parcial |
| L-PV-04 | medio | Sí (wiring trivial) | No |
| L-PV-05 | medio | Sí (instanciar ContractValidator) | No |
| L-PV-06 | bajo-medio | Sí | No |
| L-PV-07 | medio | Sí (integrar MinOnOffTimer) | No |
| L-PV-08 | medio | Requiere modelo cooling | No |
| L-PV-09 | medio | Requiere modelo dehumidification | No |
| L-PV-10 | bajo | No accionable (es por diseño) | No |
| L-PV-11 | bajo | Solo documentación | No |
| L-PV-12 | bajo | Post-v1 | No |
| L-PV-13 | bajo | Post-v1 | No |
| L-PV-14 | medio | Sí (PerturbationEngine) | No |
| L-PV-15 | medio | Parcial (stuck/drift fáciles) | No |
| L-PV-16 | medio | Sí (métricas en `metrics.py`) | No |
| L-PV-17 | medio | Sí (Flux task) | No |
| L-PV-18 | **High** (telemetry_events bucket) | Sí (1 línea init + 2º mqtt_consumer) | Parcial (cobertura producción) |
| L-PV-19 | medium (state_events measurement) | Sí (eliminar name_override) | No |
| L-PV-20 | medium (streams cmd/ack/event) | Parcial (event para faults) | No |
| L-PV-21 | **High** (captia_metadata vacío) | Sí (bootstrap script) | **Sí (rollups no funcionan)** |
| L-PV-22 | medium (routing on-change) | Sí (extender tagpass) | No |
| L-PV-23 | medium (OUTDOOR asset) | Sí (configuración) | No |
