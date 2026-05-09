# Schema canónico InfluxDB

> **Última verificación:** 2026-05-10
> **Fuente de verdad:** `docs/specs/synthetic-bms/02-domain-spec.md`.

## Measurement

Toda la telemetría continua de CENTINELA+ vive en un único measurement:

- `captia_point` — telemetría continua y on-change.
- `captia_fault_labels` — etiquetas de fallo (Caso C, no contamina).
- `captia_point_meta` — catálogo de variables (en bucket `captia_metadata`).

## Tags canónicos (5)

| Tag | Cardinalidad | Ejemplo |
|---|---|---|
| `captia_env` | 3 | `dev` / `staging` / `prod` |
| `domain_id` | 1–5 | `bms_classrooms`, `bms_buildings`, `weather_station`, `traffic_cameras`, `hvac_system` |
| `site_id` | 1–N | `ies_simarro`, `bdg2_education`, `xativa`, `valencia`, `lbnl_building59` |
| `asset_id` | 1–70 por site | `AULA01..AULA70`, `bdg2_bldg_XX`, `era5_gridpoint`, `DGT_CAM_*`, `RTU_01` |
| `variable` | 24+ | `co2`, `temperature_01`, `power_01`, ... |

## Field

- `value` (float, único). Estados booleanos: `0.0` o `1.0`.

## Buckets y retenciones

| Bucket | Retención | Origen |
|---|---|---|
| `telemetry` | 14 d | Live raw (5 s) |
| `telemetry_1m` | 30 d | Downsample 1 min |
| `telemetry_15m` | 90 d | Downsample 15 min |
| `telemetry_1h` | 365 d | Downsample horario, principal para ML |
| `state_events` | 90 d | On-change (señales `_state`, `_cmd`, `_sp`) y `captia_fault_labels` |
| `telemetry_events` | 90 d | Eventos del sistema (no telemetría) |
| `captia_metadata` | infinito | Catálogo (`captia_point_meta`) |

## Line protocol

Plantilla para una lectura continua:

```
captia_point,captia_env=dev,domain_id=bms_classrooms,site_id=ies_simarro,asset_id=AULA01,variable=co2 value=712.0 1714572345000000000
```

Plantilla para una etiqueta de fallo Caso C (`active` int + `severity` float):

```
captia_fault_labels,captia_env=dev,domain_id=hvac_system,site_id=lbnl_building59,asset_id=RTU_01,fault_type=valve_stuck active=1i,severity=0.74 1714572345000000000
captia_fault_labels,captia_env=dev,domain_id=hvac_system,site_id=lbnl_building59,asset_id=RTU_01,fault_type=valve_stuck active=0i 1714578345000000000
```

## Routing on-change vs continuo

| `metric_kind` | Tipo | Stats rollup | Bucket destino |
|---|---|---|---|
| `analog_gauge` | continua | mean, min, max | `telemetry` |
| `bool_presence` | continua bool | duty, count_rise, last | `telemetry` |
| `counter` | continua int acumulado | sum (delta) | `telemetry` |
| `bool_state` | on-change bool | last, count_rise | `state_events` |
| `setpoint_step` | on-change | last | `state_events` |
| `skip` | continua sin rollup | — | `telemetry` |

## Validación

```bash
scripts/verify_canonical_schema.sh
```

Ejecuta queries Flux que confirman:

- Solo un `_measurement = "captia_point"` (más `captia_fault_labels` y `captia_point_meta`).
- Los 5 tags presentes en cada serie.
- Único field `value`.
- No hay variables en `state_events` que también aparezcan en `telemetry` (excepto bool_presence que va a ambos).

## Validador Python

`notebooks/_common/captia_schema.py:validate_canonical_tags(tags)` lanza
`ValueError` si faltan tags. Usado en notebooks y tests.
