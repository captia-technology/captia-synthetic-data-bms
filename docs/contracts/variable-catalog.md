# Catálogo de variables canónicas

> **Última verificación:** 2026-05-10
> **Fuente de verdad:** `docs/specs/synthetic-bms/02-domain-spec.md` ·
> `notebooks/_common/captia_schema.py`.

Catálogo de las variables que produce el generador BMS y los notebooks
didácticos. **Nombres en underscore** — alias con guion solo se permiten en
ETL externos (tabla de equivalencias al final).

## Variables — gateway BMS aulas (`domain_id=bms_classrooms`)

| Variable | Unidad | Rango físico | metric_kind | Bucket |
|---|---|---|---|---|
| `temperature_01` | °C | 16–32 | analog_gauge | telemetry |
| `relative_humidity_01` | %RH | 20–80 | analog_gauge | telemetry |
| `co2` | ppm | 300–5000 | analog_gauge | telemetry |
| `t_voc` | ppb | 0–3000 | analog_gauge | telemetry |
| `iaq_index` | índice 0–500 | 0–500 | analog_gauge | telemetry |
| `avg_sound_level` | dB | 30–90 | analog_gauge | telemetry |
| `max_sound_level` | dB | 30–110 | analog_gauge | telemetry |
| `luminosity` | lux | 0–2000 | analog_gauge | telemetry |
| `power_01` | W | 0–3000 | counter | telemetry (sum) |
| `temperature_supply` | °C | 8–30 | analog_gauge | telemetry |
| `temperature_return` | °C | 8–32 | analog_gauge | telemetry |
| `ac_state` | bool | {0,1} | bool_state | state_events |
| `ac_control` | bool | {0,1} | bool_state | state_events |
| `fan_speed_01_state` | bool | {0,1} | bool_state | state_events |
| `fan_speed_02_state` | bool | {0,1} | bool_state | state_events |
| `fan_speed_03_state` | bool | {0,1} | bool_state | state_events |
| `light_01_state` | bool | {0,1} | bool_state | state_events |
| `light_02_state` | bool | {0,1} | bool_state | state_events |
| `valve_control` | bool | {0,1} | bool_state | state_events |
| `valve_state` | bool | {0,1} | bool_state | state_events |
| `occupancy` | bool | {0,1} | bool_presence | telemetry |
| `people_count` | int | 0–50 | analog_gauge | telemetry |

## Variables — meteorología (`domain_id=weather_station`)

| Variable | Unidad | Rango | metric_kind |
|---|---|---|---|
| `temperature_outdoor` | °C | -5–45 | analog_gauge |
| `solar_irradiance` | W/m² | 0–1100 | analog_gauge |
| `wind_speed` | m/s | 0–30 | analog_gauge |
| `precipitation` | mm | 0–100 | counter |
| `pressure` | hPa | 950–1050 | analog_gauge |
| `dewpoint` | °C | -10–35 | analog_gauge |

## Variables — tráfico (`domain_id=traffic_cameras`)

| Variable | Unidad | Rango | metric_kind |
|---|---|---|---|
| `vehicle_count` | count | 0–200 | analog_gauge |
| `congestion_level` | nivel 0–3 | 0–3 | analog_gauge |
| `detection_confidence` | float | 0.5–1.0 | analog_gauge |

## Alias guion → underscore (ETL Caso A In-Gauge → CAPTIA)

| Alias guía CENTINELA+ (con guion) | Variable canónica (underscore) |
|---|---|
| `temperature-indoor` | `temperature_01` |
| `relative-humidity` | `relative_humidity_01` |
| `t-voc` | `t_voc` |
| `iaq-index` | `iaq_index` |
| `avg-sound-level` | `avg_sound_level` |
| `max-sound-level` | `max_sound_level` |
| `people-count` | `people_count` |

## Catálogo `captia_point_meta`

Se publica al inicio del stack en el bucket `captia_metadata`. Cada
variable canónica produce una línea como:

```
captia_point_meta,captia_env=dev,domain_id=bms_classrooms,site_id=ies_simarro,asset_type=classroom,variable=co2 metric_kind="analog_gauge",unit="ppm",range_min=300,range_max=5000,data_type="float"
```

Sin `captia_point_meta` poblado, las tareas Flux de downsampling no emiten
para esa variable. Ver `infra/influxdb/init/init_buckets_tasks.sh`.
