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
- 16-21 variables por aula.
- Independencia: cada aula tiene `np.random.default_rng(seed + asset_idx)` para sub-RNG independiente y reproducible.

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

### Catálogo `captia_metadata`

Para cada variable se publica al bucket `captia_metadata` (retención infinita) un registro con:

```
captia_metadata,domain_id=bms_classrooms,asset_id=AULA01,variable=co2
  unit="ppm",rango_min=300,rango_max=5000,metric_kind="analog_gauge"
```

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

Cada evento de fallo genera serie en bucket `state_events` (90 d retención) con:

```
captia_point,captia_env=dev,domain_id=bms_classrooms,site_id=ies_simarro,asset_id=AULA03,variable=fault.valve_stuck
  value=1.0  <- durante el episodio
  value=0.0  <- al terminar
```

Esto permite training supervisado (Caso C) y queries Flux para clasificación.

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
