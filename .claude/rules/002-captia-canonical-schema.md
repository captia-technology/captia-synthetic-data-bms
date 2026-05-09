# Regla 002 — Schema canónico CAPTIA

## Source of truth

`docs/CENTINELA_Guia_Alumnos_v4.md:141-180` y `docs/specs/synthetic-bms/02-domain-spec.md`.

## Contrato inmutable

- **Measurement (telemetría continua)**: `captia_point`.
- **Field**: `value` (float; estados booleanos como `1.0`/`0.0`).
- **Tags (5)**: `captia_env`, `domain_id`, `site_id`, `asset_id`, `variable`.
- **Topic MQTT telemetría**: `captia/{env}/{tenant}/{site}/{device}/telemetry/{name}`.
- **Topic MQTT eventos**: `captia/{env}/{tenant}/{site}/{device}/event/{name}`.
- **Payload JSON**: `{"value": <float>, "ts_ns": <epoch_ns>}`.

## Buckets InfluxDB y retenciones

| Bucket | Retención | Origen |
|--------|-----------|--------|
| `telemetry` | 14 días | Live raw |
| `telemetry_1m` | 30 días | Downsample task |
| `telemetry_15m` | 90 días | Downsample task |
| `telemetry_1h` | 365 días | Downsample task |
| `state_events` | 90 días | On-change dedup |
| `captia_metadata` | infinito | Catálogo |

## Validación

`scripts/verify_canonical_schema.sh` ejecuta queries Flux que confirman tags presentes y measurement único.

## Anti-patrón

- Cambiar nombres de tags o measurement por conveniencia local.
- Usar otro field name que no sea `value`.
- Topics planos sin la estructura jerárquica.
