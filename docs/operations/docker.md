# Operación con Docker Compose

> **Última verificación:** 2026-05-10
> **Reglas vinculantes:** `.claude/rules/004-docker-compose-conventions.md`.

## Layouts

El stack se compone de **4 ficheros** Compose:

| Fichero | Servicios | Cuándo usar |
|---|---|---|
| `compose/base.yaml` | mosquitto, influxdb, redis, telegraf, grafana | siempre |
| `compose/observability.yaml` | prometheus, loki, promtail | recomendado |
| `compose/generator.yaml` | bms-data-generator | siempre que generes datos |
| `compose/data-plane-init.yaml` | init de buckets + tasks Flux | una vez al primer arranque |

El `Makefile` los compone con `-f` por orden:

```bash
make demo
# = docker compose -f compose/base.yaml -f compose/observability.yaml \
#                  -f compose/generator.yaml -f compose/data-plane-init.yaml \
#                  up --build -d
```

## Orden de arranque

1. `mosquitto`, `influxdb`, `redis` (sin dependencias).
2. `telegraf` (depende de mosquitto + influxdb healthy).
3. `bms-data-generator` (depende de redis + influxdb).
4. `data-plane-init` (one-shot: inicializa buckets, tasks Flux,
   `captia_point_meta`).
5. `grafana`, `prometheus`, `loki`, `promtail` (lectores).

`depends_on: condition: service_healthy` evita arranques prematuros.

## Healthchecks

Cada servicio persistente tiene healthcheck. Validar con:

```bash
docker compose ps
# todos deben aparecer (healthy)
```

## Reglas de imágenes

- **Tags fijos**: nunca `latest`.
- Versión actual:
  - `eclipse-mosquitto:2.0.18`
  - `influxdb:2.7`
  - `redis:7-alpine`
  - `telegraf:1.32`
  - `grafana/grafana:11.4.x` (Dockerfile custom).

## Recursos

| Servicio | mem_limit | cpus |
|---|---|---|
| mosquitto | 256m | 0.5 |
| influxdb | 1g | 1.0 |
| redis | 256m | 0.5 |
| telegraf | 256m | 0.5 |
| grafana | 512m | 1.0 |
| bms-data-generator | 512m | 1.0 |

## Comandos útiles

```bash
# Levantar todo (~ 90 s)
make demo

# Solo base
docker compose -f compose/base.yaml up -d

# Logs en vivo
docker compose logs -f telegraf

# Apagar y limpiar volúmenes
make down-clean         # ¡borra datos!

# Estado
docker compose ps
task smoke               # healthcheck endpoints
```

## Persistencia

Volúmenes nombrados (no anonymous):

- `mosquitto_data`, `mosquitto_log`.
- `influxdb_data`, `influxdb_config`.
- `redis_data`.
- `telegraf_state` (durabilidad de buffer).
- `grafana_data`.

Para hacer backup:

```bash
docker run --rm -v captia-bms_influxdb_data:/data \
  -v $(pwd)/backup:/backup alpine \
  tar czf /backup/influxdb_$(date +%Y%m%d).tgz -C /data .
```
