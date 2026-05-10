# 02 — Domain spec

## Context

Define el modelo de dominio BMS reutilizable por el microservicio. Fuente de verdad: `docs/CENTINELA_Guia_Alumnos_v4.md` (líneas 30-180, 282-290) y módulo `vendor/synthetic-generator/domains/bms_classrooms/`.

## Definición

**BMS = Building Management System**, en el contexto educativo IES Simarro. El gateway BMS publica telemetría de aulas a frecuencia 5 s.

Cita: `docs/CENTINELA_Guia_Alumnos_v4.md:59` (ver `00-research-report.md` sección 2).

## Schema canónico CAPTIA (REGLA 002, INMUTABLE)

### Telemetría continua

```
measurement: captia_point
tags (5):
  captia_env  ∈ {dev, staging, prod}
  domain_id   = "bms_classrooms"
  site_id     = "ies_simarro"
  asset_id    ∈ {AULA01, AULA02, ..., AULA70}
  variable    ∈ <ver tabla de variables>
field:
  value: float
timestamp: ns epoch
```

### Topic MQTT

```
captia/{captia_env}/{captia_tenant}/{site_id}/{asset_id}/telemetry/{variable}
captia/{captia_env}/{captia_tenant}/{site_id}/{asset_id}/event/{variable}
```

### Payload JSON

```json
{"value": 712.3, "ts_ns": 1715260800000000000}
```

## Entidades

### Site

- `site_id = "ies_simarro"` (único en v1).
- Ubicación geográfica: Xàtiva, Valencia (zona Köppen Csa).
- Calendario lectivo: Comunidad Valenciana 2025-2026.

### Asset (aula)

- `asset_id` ∈ `{AULA01..AULA10}` por defecto (configurable hasta `AULA70` vía `BMS_N_AULAS`).
- **33 variables emitidas por aula**: 21 generadas por el vendor `synthetic-generator` (renombradas vendor → `production_name` en `variables.yaml`) + **12 derivadas** declarativamente en `config/domains/bms_classrooms/derivations.yaml` (transforms: `passthrough`, `jitter`, `linear`, `bool_to_speed`, `bool_to_intensity`, `threshold_to_bool`). Cubren las 30 variables canónicas del PPTX `simarro-prod` slide 14.
- Independencia: cada aula tiene `np.random.default_rng(seed + asset_idx)` para sub-RNG independiente y reproducible. Las derivations añaden RNG sub-deterministic por `(name, asset, ts_5s_bucket)` para jitter reproducible dentro de la misma ventana.

### Variable (`metric_kind`)

| Variable | Tipo | Unidad | Rango físico | metric_kind |
|----------|------|--------|--------------|-------------|
| `temperature_01` | continua | °C | 16-32 | analog_gauge |
| `relative_humidity_01` | continua | %RH | 20-80 | analog_gauge |
| `co2` | continua | ppm | 300-5000 | analog_gauge |
| `t_voc` | continua | ppb | 0-3000 | analog_gauge |
| `iaq_index` | continua | índice 0-500 | analog_gauge |
| `avg_sound_level` | continua | dB | 30-90 | analog_gauge |
| `max_sound_level` | continua | dB | 30-110 | analog_gauge |
| `luminosity` | continua | lux | 0-2000 | analog_gauge |
| `power_01` | continua | W | 0-3000 | counter |
| `temperature_supply` | continua | °C | 8-30 | analog_gauge |
| `temperature_return` | continua | °C | 8-32 | analog_gauge |
| `solar_irradiance` | continua (sitio) | W/m² | 0-1100 | analog_gauge |
| `temperature_outdoor` | continua (sitio) | °C | -5-45 | analog_gauge |
| `ac_state` | on-change | bool {0,1} | bool_state |
| `ac_control` | on-change | bool {0,1} | bool_state |
| `fan_speed_01_state` | on-change | bool {0,1} | bool_state |
| `fan_speed_02_state` | on-change | bool {0,1} | bool_state |
| `fan_speed_03_state` | on-change | bool {0,1} | bool_state |
| `light_01_state` | on-change | bool {0,1} | bool_state |
| `light_02_state` | on-change | bool {0,1} | bool_state |
| `valve_control` | on-change | enum {0,1} | bool_state |
| `valve_state` | on-change | enum {0,1} | bool_state |
| `occupancy` | on-change | bool {0,1} | bool_presence |
| `people_count` | continua | int 0-50 | analog_gauge |

### Catálogo `captia_point_meta` (en bucket `captia_metadata`)

Conforme a `docs/influxdb-simarro-buckets.pptx` slide 9 (mapeo simarro-prod
septiembre 2026), el catálogo de variables vive en el measurement
**`captia_point_meta`** dentro del bucket `captia_metadata` (retención
infinita). Cada registro:

```
captia_point_meta,captia_env=dev,domain_id=bms_classrooms,site_id=ies_simarro,asset_type=classroom,variable=co2
  metric_kind="analog_gauge",storage_mode="continuous",data_type="float",
  unit="ppm",point_type="sensor",category="ENVIRONMENTAL",
  range_min=400,range_max=2200,vendor_name="co2"
```

Tags: `captia_env`, `domain_id`, `site_id`, `asset_type`, `variable` (donde
`variable` lleva el nombre **de producción**: `temperature_01`,
`relative-humidity`, etc.).

Fields: `metric_kind`, `storage_mode`, `data_type`, `unit`, `point_type`,
`category`, `range_min`, `range_max`, `vendor_name` (cuando hay alias
vendor → producción).

El catálogo es **a nivel de dominio** (no por `asset_id`): todas las aulas
del mismo `domain_id` comparten el mismo perfil de variables. La carga la
realiza `infra/influxdb/init/init_buckets_tasks.sh` durante `make demo`,
leyendo `config/domains/<domain_id>/variables.yaml` y emitiendo
line-protocol con `influx write`. Sin estos registros, las tareas Flux de
downsampling tier-1 no emiten a `telemetry_1m` (allowlist por
`metric_kind`, regla CENTINELA+ § 1.3 / § 1.4).

> Compatibilidad: durante un periodo transitorio (T-PV-23) el script init
> también limpia el measurement legacy `captia_metadata` para que un
> bucket existente con esquema antiguo no quede con registros huérfanos
> tras un upgrade.

### Naming de variables — alias guion ↔ underscore

`docs/CENTINELA_Guia_Alumnos_v4.md` mezcla los dos estilos: línea 59 usa
`temperature_01`, `co2`, `t-voc`, `iaq-index`; línea 416-424 (mapping Caso A)
usa `temperature-indoor`, `relative-humidity`. Para evitar quoting de Flux y
mantener compatibilidad con el resto del schema (`captia_env`, `domain_id`,
`asset_id` siempre con underscore), este repo normaliza **todo a
underscore**. ETL externos (Caso A In-Gauge → CAPTIA) deben usar la tabla
de equivalencias siguiente al ingestar:

| Alias guía CENTINELA+ (con guion) | Variable canónica (con underscore, este repo) |
|-----------------------------------|----------------------------------------------|
| `temperature-indoor`              | `temperature_01`                             |
| `relative-humidity`               | `relative_humidity_01`                       |
| `t-voc`                           | `t_voc`                                      |
| `iaq-index`                       | `iaq_index`                                  |
| `avg-sound-level`                 | `avg_sound_level`                            |
| `max-sound-level`                 | `max_sound_level`                            |
| `people-count`                    | `people_count`                               |

## Reglas de generación

### Escala temporal

- **Frecuencia raw**: 5 s (telemetría continua).
- **State events**: emitidos solo on-change (Telegraf statefile dedup).
- **Backfill default**: 30 días (configurable hasta 365).
- **Live**: `lookahead_hours=1`, regenerate on exhaustion.

### Determinismo

- `seed=42` por defecto, configurable vía `BMS_SEED`.
- `numpy.random.default_rng(seed)` (NO `np.random.seed()`).
- Sub-RNGs por aula: `rng_aula = np.random.default_rng(seed + asset_idx)`.

### Calendario lectivo

- Lunes-Viernes 08:00-15:00 (zona horaria `Europe/Madrid`).
- Vacaciones 2025-2026 (Comunidad Valenciana):
  - Navidad: 22-dic-2025 → 7-ene-2026.
  - Fallas: 14-mar-2026 → 19-mar-2026.
  - Semana Santa: 4-abr-2026 → 12-abr-2026.
  - Verano: 20-jun-2026 → 7-sep-2026.

### Modelos físicos (defaults literatura)

| Parámetro | Valor default | Fuente | Override |
|-----------|--------------|--------|----------|
| `co2_rise_rate_per_person_per_min` | 4.5 ppm/persona/min | ASHRAE 62.1, EN 16798 | `bms_calibration.physics_overrides` |
| `hvac_response_time_minutes` | 8 min | Literatura | `bms_calibration.physics_overrides` |
| `temp_outdoor_indoor_coupling` | 0.15 | Envolvente típica | `bms_calibration.physics_overrides` |
| `occupancy_secondary_school_50_students` | Poisson + horario | Heurística | `extensions/bms_calibration` |

### Períodos sin clase

- Fines de semana, vacaciones: `occupancy=0`, HVAC `standby` (válvulas cerradas, fans off).
- Valores físicos siguen reglas (Tª responde a exterior, lux sigue daylight). NO usar `NaN`.

## Modelo de fallos HVAC (Caso C, ADR-010)

4 tipos en v1, configurables vía `config/domains/bms_classrooms/faults.yaml`:

| Fault type | Materialización | Variables afectadas |
|-----------|----------------|--------------------|
| `sensor_drift` | Bias acumulativo gaussiano sobre lectura | `temperature_supply`, `temperature_return` |
| `valve_stuck` | `valve_state` permanece en último estado durante `duration_minutes` | `valve_state`, `temperature_supply` |
| `fan_failure` | `fan_speed_*_state=0` y power_01 caído | `fan_speed_*`, `power_01` |
| `refrigerant_low` | `temperature_supply` ≈ `temperature_return` (no enfría) | `temperature_supply` |

### Etiquetado de fallos

Conforme a `docs/CENTINELA_Guia_Alumnos_v4.md:464` (Caso C — *"las etiquetas de
fallo no van en InfluxDB junto a la telemetría: van en lakeFS o en un
measurement separado `captia_fault_labels`"*), las etiquetas se materializan
en un measurement dedicado **`captia_fault_labels`** dentro del bucket
`state_events` (90 d de retención).

Schema:

```
captia_fault_labels,captia_env=dev,domain_id=bms_classrooms,site_id=ies_simarro,asset_id=AULA03,fault_type=valve_stuck
  active=1.0i,severity=0.74    <- al iniciar el episodio (timestamp = start)
  active=0.0i                  <- al terminar (timestamp = end)
```

Tags: los 4 tags canónicos (`captia_env`, `domain_id`, `site_id`, `asset_id`)
más `fault_type` (uno de los 4 tipos del catálogo).

Fields: `active` (bool 0/1) marca el inicio/fin del episodio; `severity`
(float ∈ [0.3, 1.0]) acompaña al evento de inicio.

Esta separación mantiene `captia_point` libre de etiquetas no-canónicas y
permite que un consumidor entrene clasificadores supervisados con un
único `from(bucket:"state_events") |> filter(fn:(r) => r._measurement ==
"captia_fault_labels")`.

## Acceptance criteria

| ID | Criterio | Validación |
|----|----------|-----------|
| DC-01 | Cada DataPoint emitido cumple schema canónico | `tests/integration/test_canonical_schema.py` |
| DC-02 | `seed=42` produce hash sha256 idéntico en 2 runs | `tests/snapshot/test_bms_classrooms_snapshot.py` |
| DC-03 | Calendario lectivo correcto para 4 fechas (lectivo, weekend, navidad, verano) | `extensions/bms_calibration/tests/test_school_calendar.py` |
| DC-04 | Fault injection genera ≥ 4 tipos cuando `faults_enabled=true` | `tests/integration/test_faults.py` |
| DC-05 | `captia_metadata` poblado para todas las variables | Query Flux post-init |

## Open questions

Ver `00-open-questions.md` (especialmente L-01 calibración real).
