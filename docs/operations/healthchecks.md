# Operaciones — Healthchecks

> **Última verificación:** 2026-05-10
> **Cierra:** H-19 (`docs/audit/AUDIT_REPORT.md`).
> **Source:** [`compose/base.yaml`](https://github.com/captiatechnology/CAPTIA-SYNTHETIC-DATA-BMS/blob/main/compose/base.yaml) · [`compose/observability.yaml`](https://github.com/captiatechnology/CAPTIA-SYNTHETIC-DATA-BMS/blob/main/compose/observability.yaml) · [`compose/generator.yaml`](https://github.com/captiatechnology/CAPTIA-SYNTHETIC-DATA-BMS/blob/main/compose/generator.yaml).

## Convención

- **HTTP** disponible → `curl -fsS http://localhost:PORT/PATH` (preferido).
- **Imagen sin `curl` pero con `wget`** (BusyBox-style: Prometheus, Loki) →
  `wget -qO- http://localhost:PORT/PATH`.
- **CLI nativo** del servicio → cuando es más fiable que probe HTTP
  (Mosquitto sin endpoint HTTP, Redis con `redis-cli ping`).
- **Always**: `interval: 30s` · `timeout: 5–10s` · `retries: 3–5` · primer
  arranque con `start_period` 15–60 s.

## Tabla de healthchecks

| Servicio | Probe | Verifica | Tipo |
|---|---|---|---|
| `mosquitto` | `mosquitto_sub -h localhost -t '$SYS/broker/uptime' -C 1 -W 5` | broker acepta conexiones MQTT | CLI |
| `influxdb` | `curl -fsS http://localhost:8086/health` | API + storage OK | HTTP |
| `redis` | `redis-cli ping` (espera `PONG`) | proceso responde | CLI |
| `telegraf` | `curl -fsS http://localhost:9273/metrics \| head -1 \| grep -q '^# HELP'` | Prometheus output exporta métricas (no solo proceso vivo — H-02) | HTTP |
| `grafana` | `curl -fsS http://localhost:3000/api/health` | UI + datasources cargados | HTTP |
| `prometheus` | `wget -qO- http://localhost:9090/-/healthy` | scrape loop OK | HTTP (BusyBox) |
| `loki` | `wget -qO- http://localhost:3100/ready \| grep -q ready` | ingester ready | HTTP (BusyBox) |
| `promtail` | (sin healthcheck — no expone endpoint stable) | — | N/A |
| `bms-data-generator` | `curl -fsS http://localhost:8120/healthz` | FastAPI app + lifespan | HTTP |
| `influx-init` | (one-shot job — exit code 0 indica éxito) | bucket setup completo | exit code |

## Por qué cada uno es como es

- **Mosquitto**: no tiene API HTTP nativa con health endpoint; `mosquitto_sub`
  con timeout `-W 5` recibe `$SYS/broker/uptime` (publicado cada 10 s por el
  broker mismo) y prueba round-trip MQTT real.
- **Telegraf** (PATCH H-02 / 2026-05-10): antes era `pgrep -f telegraf` que
  solo verifica que el proceso vive, no que está procesando. El nuevo probe
  asegura que `[[outputs.prometheus_client]]` (`:9273`) está sirviendo,
  lo cual implica que Telegraf parseó la config y arrancó los plugins.
- **Prometheus / Loki**: las imágenes oficiales son distroless tipo BusyBox
  y no traen `curl`. Usamos `wget -qO-` que sí está.
- **Grafana**: `/api/health` devuelve `{"database":"ok","version":"..."}` cuando
  los datasources se han provisionado correctamente.
- **Generator**: `/healthz` está cubierto por la spec
  `06-api-and-ui-spec.md` y el SLA es `< 100 ms` p99.

## Cómo bloquear hasta healthy

`make wait-healthy` (full stack) o `make wait-healthy-infra` (sin generator)
bloquean el shell hasta que `docker compose ps` reporte `healthy` para todos
los servicios persistentes. Implementado en
[`Makefile`](https://github.com/captiatechnology/CAPTIA-SYNTHETIC-DATA-BMS/blob/main/Makefile)
con timeout de 120 s.

## Cómo lo usa CI

El job `e2e-stack` en `ci.yml` ejecuta `make demo`, que invoca
`make wait-healthy-infra` + `make wait-init`. Si algún healthcheck falla,
el step falla con `make demo: target failed`, y el step posterior captura
los logs de los 9 contenedores como artifact.

## Anti-patrones

- **`pgrep -f <name>`** sin verificar endpoint — sólo confirma proceso vivo,
  no health (PATCH H-02 lo eliminó para Telegraf).
- **`exit 0` siempre** o `true` como probe — degrada a "always healthy",
  oculta drifts.
- **`interval` muy bajo** (< 10 s) — sobrecarga el servicio sin información
  adicional.
- **`start_period` ausente** en servicios con bootstrap > 30 s
  (InfluxDB, Loki) — los probe-failures iniciales se cuentan y se marca
  unhealthy de inmediato.

## Reglas de oro

> **30 s interval** + **5 s timeout** + **3–5 retries** + `start_period` ≥
> tiempo de bootstrap medido + endpoint que valide funcionalidad real
> (no solo "proceso vivo").
