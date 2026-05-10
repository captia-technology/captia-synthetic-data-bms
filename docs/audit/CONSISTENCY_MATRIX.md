# Auditoría — Matriz de consistencia BMS ↔ CAPTIA-connect

> Generado por el subagente comparador el 2026-05-09 leyendo:
> - `captia-synthetic-data-bms` (repo principal — este repositorio)
> - `captia-connect` (referencia upstream — interno)

## Resumen ejecutivo

| Área | Estado | Crítico | Justificable |
|---|---|---|---|
| 1. Topics MQTT | ✅ Match exacto | — | — |
| 2. Payload format | ⚠ **Event timestamp diverge** | **Sí** | No |
| 3. Schema InfluxDB | ✅ Match (minor `tagexclude`) | — | Sí (validación) |
| 4. Buckets | ⚠ `telemetry_events` vivo en BMS, deprecated en upstream | Depende | Sí si no se sincroniza |
| 5. Tareas Flux | ⚠ **`downsample_state_1m` lee `telemetry`, no `state_events`** | **Sí** | No |
| 6. Env vars | ⚠ MQTT auth no expuesta; `telemetry_events` hardcoded | No (dev) | Sí (simplicidad) |
| 7. Healthchecks | ✅ Funcional (Telegraf menos riguroso) | — | Sí |
| 8. Compose | ⚠ **Omite `dashboard-adapter`** (resuelto en BMS por `/v1/query`) | Sí si esperan `/api/query` | Sí, BMS es generator |
| 9. Observabilidad | ✅ Probable match (configs no leídas en detalle) | — | — |
| 10. Naming | ✅ Divergencia intencional (multi-stack isolation) | — | **Sí** |
| 11. Contratos | ✅ Respetados | — | — |

## 1. Topics MQTT — match exacto

Ambos: `captia/{env}/{tenant}/{site}/{device}/telemetry/{name}` y `.../event/{name}`.
Regex de extracción de tags coincide línea por línea (`captia_env`, `domain_id`, `site_id`, `asset_id`, `variable`, `stream`).

Suffix globs on-change idénticos en ambos `processors.clone.tagpass`:
`*_cmd`, `*_ack`, `*_status`, `*_state`, `*_st`, `*_active`, `*_enable`, `*_in_progress`, `relay_*`, `*_setpoint`, `*_sp`, `*_mode` (BMS añade además `ac_control`, `aire_state`, `fault.*` por T-PV-08/T-PV-28 — extensión).

## 2. Payload — divergencia crítica en eventos

| Stream | BMS | Upstream |
|---|---|---|
| `telemetry` | `{"value": X, "ts_ns": <unix_ns>}` | Idéntico |
| `event` | `{"value": X, "ts_ns": <unix_ns>}` | `{"ts": "2026-05-09T18:30:00.123Z", ...}` |

`infra/telegraf/telegraf.conf:75` en BMS usa `json_time_key = "ts_ns"` para ambos consumers. El upstream usa `json_time_key = "ts"` con `json_time_format = "2006-01-02T15:04:05.999Z07:00"` para events (telegraf.conf upstream línea 99-100).

**Impacto**: si un publisher CAPTIA-connect real envía un `event` JSON con `ts` ISO 8601 al broker BMS, Telegraf no parseará el timestamp y usará `now()`. Flujo sigue, fidelidad temporal se pierde.

**Acción recomendada**: añadir un segundo `[[inputs.mqtt_consumer]]` para `event` topics que use `json_time_key = "ts"` en ISO. Documentado para próxima fase.

## 3. Schema InfluxDB — match

`captia_point` (telemetry), `captia_point_state` (clone deduped), `captia_cmd_event` (events), `captia_point_meta` (catalogo).
Tags y fields canónicos idénticos. Diferencia menor: BMS no aplica `tagexclude = ["topic", "type"]` en el output `captia_cmd_event` — el tag `topic` raw persiste. No rompedor.

## 4. Buckets

| Bucket | BMS | Upstream | Match |
|---|---|---|---|
| `telemetry` | 14d | 14d | ✅ |
| `telemetry_1m` | 30d | 30d | ✅ |
| `telemetry_15m` | 90d | 90d | ✅ |
| `telemetry_1h` | 365d | 365d | ✅ |
| `state_events` | 90d | 90d | ✅ |
| `telemetry_events` | 90d (operativo, T-PV-18) | deprecated 2026-04-02 | ⚠ |
| `captia_metadata` | ∞ | ∞ | ✅ |

Si BMS y CAPTIA-connect comparten InfluxDB en producción, BMS escribirá en un bucket que upstream ya no consume. El propio `init_buckets_tasks.sh:67-71` referencia `docs/influxdb-simarro-buckets.pptx slide 8` como fuente de verdad y mantiene el bucket. **Acción recomendada**: ADR explícito justificando seguir creándolo o sincronizar con upstream.

## 5. Tareas Flux — divergencia crítica en `downsample_state_1m`

| Task | BMS source | Upstream source |
|---|---|---|
| `downsample_state_1m.flux` | `from(bucket: "state_events")` filtra `_measurement == "captia_point_state"` ← **YA CORREGIDO en commit `c306e45`** (era `captia_point` antes) | `from(bucket: "state_events")` |

**Estado actual**: corregido en línea 58/67 del archivo (`L-PV-19`). Match con upstream. ✅

Las otras 5 tareas (`analog_1m`, `counter_1m`, `presence_1m`, `15m`, `1h`) coinciden literalmente.

## 6. Variables de entorno

Diferencias notables:

- **MQTT auth ausente** en BMS (`MQTT_USER`/`MQTT_PASSWORD` no expuestos). Mosquitto en BMS opera con `allow_anonymous true` marcado como **dev-only** en `infra/mosquitto/mosquitto.conf` y `SECURITY.md`. En upstream sí se expone para integrar con TLS port 8883.
- **`INFLUXDB_BUCKET_TELEMETRY_EVENTS`** hardcoded en BMS (`telemetry_events`); upstream lo expone configurable.
- **`TELEGRAF_CONTROLLER_*`**: BMS no incluye output `outputs.heartbeat` (eliminado por simplificación; ver comentario top-of-file en `infra/telegraf/telegraf.conf`).
- **`BMS_*`** (domain-specific): extensión legítima (no rompedora).

## 7. Healthchecks

| Servicio | BMS | Upstream | Equivalencia |
|---|---|---|---|
| mosquitto | `CMD-SHELL mosquitto_sub` | `CMD mosquitto_sub` | ✅ funcional |
| influxdb | `curl /health` | `influx ping` | ✅ funcional |
| redis | `redis-cli ping` | idem | ✅ exacto |
| telegraf | `pgrep -f telegraf` | `wget :9273/metrics` | ⚠ menos riguroso (proceso vivo ≠ ingesta saludable) |
| grafana | `curl /api/health` | idem | ✅ exacto |
| prometheus | `wget /-/healthy` | (no en upstream base) | extensión |
| loki | `wget /ready` | (no en upstream base) | extensión |

**Acción recomendada**: actualizar Telegraf healthcheck a `wget -qO- localhost:9273/metrics | head -1` para alinear con upstream.

## 8. Compose — omite `dashboard-adapter`

Upstream tiene un `modules/dashboard-adapter/` con FastAPI exponiendo `/v1/query`, cache Redis y selector de bucket por rango. BMS no lo vendoriza pero **implementa el contrato equivalente** en `modules/bms-data-generator/src/bms_data_generator/{services/query_service.py, api/query.py}` (gap #5 cerrado en commit `c6b8452`).

**Cobertura**: bucket selector por rango ✅, Flux builder ✅, REST POST `/v1/query` ✅, Bearer auth ✅. **Falta**: cache Redis (TODO documentado en `query_service.py`).

## 9. Observabilidad

Patrón compatible: Prometheus scrape de Telegraf `:9273`, Loki + Promtail con label `compose_project=captia-bms`, Grafana con datasources provisionados. Configs no inspeccionadas línea-a-línea por el agente; auditar `infra/prometheus/prometheus.yml`, `infra/loki/loki-config.yml`, `infra/promtail/promtail-config.yml` en una pasada posterior.

## 10. Naming — divergencia intencional

| Recurso | BMS | Upstream |
|---|---|---|
| Container prefix | `captia-bms-*` | `captia-*` |
| Compose project name | `captia-bms` | `captia` |
| Network | `captia-bms-network` | `captia-network` |

Justificado en `.env.example` (Multi-stack isolation: permitir que CAPTIA-connect upstream y BMS corran en el mismo host sin colisiones de nombre). Sin esto, no podríamos haber arrancado el BMS en una máquina que ya tenía CAPTIA-connect (ese fue exactamente el bug que detectamos en el primer `make demo`, aún antes de esta auditoría).

## 11. Contratos respetados

- Topic structure 7-segments ✅
- Schema canónico InfluxDB ✅
- Convención on-change suffix globs ✅
- Dedup `interval = 168h` ✅
- `captia_point_meta` schema ✅
- Cascada Flux 1m → 15m → 1h con preservación de `stat` tag ✅

## Top 5 desviaciones críticas

1. **Event payload `ts_ns` vs `ts` ISO** — rompe interoperabilidad de eventos.
2. **`telemetry_events` mantenido en BMS** vs deprecated upstream — divergencia de bucket.
3. **Omisión de Telegraf Controller heartbeat** — sin observabilidad central de agentes.
4. **Telegraf healthcheck `pgrep`** vs `wget metrics` — menos riguroso.
5. **`AliasSinkAdapter` de BMS** (T-PV-21) — extensión propia no presente en upstream; mantener documentada como ADR-018+ para próximas iteraciones.

## Top 5 desviaciones aceptables

1. Container/network naming con prefijo `bms-` — multi-stack isolation.
2. Stack observability completo (Prometheus + Loki + Promtail) — extensión positiva.
3. Variables `BMS_*` específicas del generator.
4. Soporte forward de `captia_version` segment en topic — no rompedor.
5. Init script en shell awk vs metadata-bootstrap Python upstream — output schema idéntico.
