# Buckets InfluxDB y retenciones

CENTINELA+ usa 7 buckets:

| Bucket | Retención | Origen |
|---|---|---|
| `telemetry` | 14 días | Live raw (5s) |
| `telemetry_1m` | 30 días | Downsample 1 min |
| `telemetry_15m` | 90 días | Downsample 15 min |
| `telemetry_1h` | 365 días | Downsample horario, principal para ML |
| `state_events` | 90 días | On-change dedup (señales `_state`, `_cmd`, `_sp`) |
| `telemetry_events` | 90 días | Eventos del sistema (no telemetría) |
| `captia_metadata` | infinito | Catálogo de variables (`captia_point_meta`) |

Las tareas Flux de downsampling se disparan periódicamente y leen del
catálogo (`captia_point_meta`) para decidir qué stat aplicar (`mean`,
`min`, `max`, `sum`, `last`, `count_rise`, `duty`).
