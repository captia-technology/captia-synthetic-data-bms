# 04 — Infrastructure spec

## Context

El stack Docker debe ser autocontenido (decisión usuario) y replicar las convenciones de `C:\CAPTIA\CAPTIA-CONNECT\captia-connect\compose\base.yaml`. Reutiliza configuraciones literales de Mosquitto, Telegraf y data-plane (Flux tasks).

## Compose layout

| Archivo | Propósito |
|---------|-----------|
| `compose/base.yaml` | Servicios persistentes: mosquitto, influxdb, redis, telegraf, grafana |
| `compose/observability.yaml` | prometheus, loki, promtail |
| `compose/generator.yaml` | bms-data-generator |
| `compose/data-plane-init.yaml` | influx-init (one-shot job) |

Merge vía `COMPOSE_FILE` env (Windows separador `;`, Linux `:`).

## Servicios

### Mosquitto 2.0.18

- **Imagen**: `eclipse-mosquitto:2.0.18`.
- **Puertos**: `${MQTT_PORT_HOST:-1884}:1883`, `${MQTT_WS_PORT_HOST:-9002}:9001`.
- **Volúmenes**: `mosquitto_data`, `mosquitto_log`, config bind `./infra/mosquitto/mosquitto.conf:ro`.
- **Healthcheck**: `mosquitto_sub -h localhost -t '$$SYS/broker/uptime' -C 1 -W 5`.
- **Config**: copia literal de `C:\CAPTIA\CAPTIA-CONNECT\captia-connect\modules\ingest\mosquitto\mosquitto.conf`.

### InfluxDB 2.7

- **Imagen**: `influxdb:2.7`.
- **Puerto**: `${INFLUXDB_PORT_HOST:-8087}:8086`.
- **Env requeridas**: `DOCKER_INFLUXDB_INIT_TOKEN`, `DOCKER_INFLUXDB_INIT_PASSWORD` (fail-fast con `:?required`).
- **Healthcheck**: `curl -fsS http://localhost:8086/health`.
- **Volúmenes**: `influxdb_data`, `influxdb_config`.

### Redis 7

- **Imagen**: `redis:7-alpine`.
- **Comando**: `redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru`.
- **Healthcheck**: `redis-cli ping`.

### Telegraf 1.32

- **Imagen**: `telegraf:1.32`.
- **Volumen config**: `./infra/telegraf/telegraf.conf:/etc/telegraf/telegraf.conf:ro`, `telegraf_state` para statefile dedup.
- **Healthcheck**: `pgrep -f telegraf`.
- **`depends_on`**: mosquitto + influxdb (`condition: service_healthy`).
- **Config**: copia literal de `C:\CAPTIA\CAPTIA-CONNECT\captia-connect\modules\ingest\telegraf\telegraf.conf` con regex tags y schema canónico exactos.

### Grafana 11.4

- **Imagen**: build local `captia-bms-grafana:local` en `infra/grafana/Dockerfile` (FROM `grafana/grafana:11.4.0` + plugin `redis-datasource`).
- **Puerto**: `${GRAFANA_PORT_HOST:-3001}:3000`.
- **Env**: `GF_SECURITY_ADMIN_*`, `GF_LIVE_HA_ENGINE=redis`.
- **Volúmenes**: provisioning, dashboards, `grafana_data`.
- **Healthcheck**: `curl -fsS http://localhost:3000/api/health`.

### Prometheus v2.49.1

- **Imagen**: `prom/prometheus:v2.49.1`.
- **Config**: `./infra/prometheus/prometheus.yml`.
- **Retention**: 7 días.
- **Scrape jobs**: prometheus, bms-data-generator:8120, telegraf:9273, influxdb:8086.

### Loki 2.9.4

- **Imagen**: `grafana/loki:2.9.4`.
- **Config**: `./infra/loki/loki-config.yml`.
- **Retention**: 30 días.

### Promtail 2.9.4

- **Imagen**: `grafana/promtail:2.9.4`.
- **Scrape**: Docker socket `com.docker.compose.project=captia-bms`.
- **Pipeline**: JSON parse para `bms-data-generator`.

### bms-data-generator

- **Build**: `modules/bms-data-generator/Dockerfile` multi-stage.
- **Puerto**: `${BMS_GENERATOR_PORT_HOST:-8120}:8120`.
- **Env**: ver tabla en `.env.example`.
- **`depends_on`**: mosquitto, influxdb, redis, telegraf (`condition: service_healthy`).
- **Healthcheck**: `curl -fsS http://localhost:8120/healthz`.
- **Volúmenes**: `./config:/app/config:ro`, `bms_output:/app/output`.

### influx-init (one-shot)

- **Imagen**: `influxdb:2.7` (CLI).
- **Restart**: `"no"`.
- **Entrypoint**: `/scripts/init_buckets_tasks.sh`.
- **Crea**: 6 buckets + 5 tareas Flux.

## Buckets InfluxDB

| Bucket | Retención | Origen |
|--------|-----------|--------|
| `telemetry` | 14 días | Live raw (telegraf ingesta directa) |
| `telemetry_1m` | 30 días | Tarea Flux `downsample_analog_1m.flux` + `downsample_state_1m.flux` + `downsample_presence_1m.flux` + `downsample_counter_1m.flux` |
| `telemetry_15m` | 90 días | Tarea Flux `downsample_15m.flux` |
| `telemetry_1h` | 365 días | Tarea Flux `downsample_1h.flux` |
| `state_events` | 90 días | Telegraf con statefile dedup on-change |
| `captia_metadata` | infinito | Catálogo de variables (poblado al arranque) |

## Volúmenes nombrados

| Volumen | Servicio | Propósito |
|---------|----------|-----------|
| `mosquitto_data` | mosquitto | Persistencia MQTT |
| `mosquitto_log` | mosquitto | Logs |
| `influxdb_data` | influxdb | Datos TSDB |
| `influxdb_config` | influxdb | Config persistente |
| `redis_data` | redis | AOF persistence |
| `telegraf_state` | telegraf | Statefile dedup on-change |
| `grafana_data` | grafana | DB Grafana, plugins |
| `prometheus_data` | prometheus | TSDB Prometheus |
| `loki_data` | loki | Logs Loki |
| `bms_output` | bms-data-generator | Dumps line-protocol |

## Red Docker

- `captia-network` (declarada en `compose/base.yaml` como `default`).
- DNS interno: `<container_name>:<port>` (ej. `mosquitto:1883`, `influxdb:8086`).

## Container naming convention

- Prefijo `captia-bms-*` para diferenciar de CAPTIA-CONNECT (que usa `captia-*`):
  - `captia-bms-mosquitto`, `captia-bms-influxdb`, `captia-bms-redis`, `captia-bms-telegraf`, `captia-bms-grafana`, `captia-bms-prometheus`, `captia-bms-loki`, `captia-bms-promtail`, `captia-bms-generator`, `captia-bms-influx-init`.

## Variables de entorno (resumen)

Ver `.env.example` para catálogo completo agrupado por servicio.

Variables fail-fast (sin default):
- `INFLUXDB_TOKEN`
- `INFLUXDB_ADMIN_PASSWORD`
- `BMS_API_TOKEN`

Variables con default sensato vía `${VAR:-default}`:
- Puertos host, niveles log, hosts internos.

## Acceptance criteria

| ID | Criterio | Validación |
|----|----------|-----------|
| IN-01 | `task up` completa en ≤ 90 s con todos los servicios `healthy` | `docker compose ps` muestra `(healthy)` en cada servicio |
| IN-02 | Tags de imagen son fijos (no `latest`) | `grep -nE "image:.*latest" compose/*.yaml` vacío (excepción: build local OK) |
| IN-03 | `${VAR:-default}` usado en variables expuestas | grep en compose archivos |
| IN-04 | `depends_on: condition: service_healthy` en consumidores | grep en compose archivos |
| IN-05 | Sin secretos hardcodeados | `git grep -nE "password=\\|token=" compose/` solo muestra placeholders `${VAR:?required}` |
| IN-06 | 6 buckets creados tras `influx-init` | Query `influx bucket list` |
| IN-07 | 5 tareas Flux creadas | `influx task list` |
| IN-08 | Telegraf consume topics MQTT y escribe `captia_point` en `telemetry` | `scripts/verify_canonical_schema.sh` |

## Riesgos operacionales

1. **Telegraf statefile**: si volumen `telegraf_state` se borra, se pierde dedup on-change. Mitigación: backup periódico.
2. **InfluxDB init one-shot**: contenedor permanece `Exited (0)` tras primer deploy. No es problema; documentado.
3. **Windows COMPOSE_FILE**: separador `;` (no `:`). Documentado en `.env.example`.
