# Troubleshooting

> **Última verificación:** 2026-05-10
> **Documento existente histórico:** [TROUBLESHOOTING.md](../TROUBLESHOOTING.md).

Esta página recoge los problemas más comunes con soluciones cortas. Para
detalle completo, ver [TROUBLESHOOTING.md](../TROUBLESHOOTING.md).

## Stack no levanta

```bash
docker compose ps
docker compose logs -f --tail=200
```

| Síntoma | Solución |
|---|---|
| InfluxDB `unhealthy` | comprueba `INFLUXDB_ADMIN_PASSWORD` y `INFLUXDB_TOKEN` en `.env`. |
| Telegraf reinicia | mira `infra/telegraf/telegraf.conf`; revisa Mosquitto health. |
| Mosquitto `unhealthy` | conflicto de puerto; cambia `MQTT_PORT_HOST`. |
| Grafana 401 | resetea `GRAFANA_ADMIN_PASSWORD`. |
| `metadata-bootstrap` falla con `connection error` | InfluxDB tarda en aceptar el token tras setup. Ya hay retry (6×5s); si persiste, `make metadata-bootstrap` manual tras el up. |

## Telegraf reporta `Wrote batch of N` pero los datos NO aparecen en bucket

**Síntoma**: `docker logs captia-bms-telegraf` muestra `[outputs.influxdb_v2] Wrote batch of N metrics in Xms` cada 10s sin errores, pero `from(bucket:"telemetry") |> range(start: -5m) |> count()` devuelve 0 (o el último point es de hace mucho tiempo).

**Causa raíz** (diagnosticada 2026-05-10): el queue persistente del broker
acumula mensajes con timestamps corruptos (residuo de bugs históricos en
publishers o procesos zombies). Cuando Telegraf reconecta con
`persistent_session = true`, el broker le entrega ese backlog. Telegraf
los procesa y POST a InfluxDB con HTTP 204, pero los puntos quedan
"outside retention policy" y se descartan **silenciosamente** (sin error
visible en métricas Telegraf).

**Fix permanente** aplicado en commit `9eba9c8`:
- `infra/telegraf/telegraf.conf`: `persistent_session = false` en ambos
  `mqtt_consumer` (telemetry + events).
- Agent sin `statefile` (estaba ligado al persistent session).
- Ver ADR-022.

**Recovery rápido si vuelve a aparecer**:

```bash
# 1. Detener job del generator (alivia el broker).
TOKEN=$(grep BMS_API_TOKEN .env | cut -d= -f2)
JOB=$(curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8121/v1/control/status | grep -oE '"job_id":"[^"]+"' | cut -d'"' -f4)
[ -n "$JOB" ] && curl -s -X POST "http://localhost:8121/v1/control/stop?job_id=$JOB" -H "Authorization: Bearer $TOKEN"

# 2. Reset profundo del broker (borra queues persistentes).
docker stop captia-bms-mosquitto captia-bms-telegraf
docker run --rm -v captia-bms_mosquitto_data:/data alpine sh -c 'rm -f /data/mosquitto.db'
docker start captia-bms-mosquitto
sleep 5
docker start captia-bms-telegraf

# 3. Verificar que un publish manual llega:
TS=$(date +%s%N)
docker exec captia-bms-mosquitto mosquitto_pub -h localhost -p 1883 \
  -t "captia/dev/bms_classrooms/ies_simarro/AULA_TEST/telemetry/temperature_01" \
  -m "{\"value\": 99.99, \"ts_ns\": $TS}"
sleep 18  # flush_interval Telegraf
TOKEN_INFLUX=$(grep INFLUXDB_TOKEN .env | cut -d= -f2)
curl -s -X POST "http://localhost:8087/api/v2/query?org=captia" \
  -H "Authorization: Token $TOKEN_INFLUX" -H "Accept: application/csv" \
  -H "Content-type: application/vnd.flux" \
  -d 'from(bucket:"telemetry") |> range(start: -1m) |> filter(fn: (r) => r.asset_id == "AULA_TEST") |> last()'
```

## Múltiples instancias del generator publicando con mismo `client_id`

**Síntoma**: Mosquitto logs muestran reconexiones cada segundo del cliente
`captia-bms-generator-demo` desde puertos distintos. Cuando varios procesos
comparten el mismo `client_id`, el broker desconecta el anterior (MQTT spec)
y entran en loop infinito de reconexiones, saturando `max_inflight_messages`
y disparando `Outgoing messages dropped`.

**Causas habituales**:
- Procesos `uvicorn bms_data_generator` zombies en el host Windows tras
  `make stream` o `make run-host` interrumpidos (búsqueda:
  `Get-Process python | Where-Object { $_.CommandLine -like '*bms_data_generator*' }`).
- Container del proyecto vecino CAPTIA-CONNECT (`captia-synth-bms`) corriendo
  en paralelo y publicando al mismo broker via `host.docker.internal:1884`.

**Fix preventivo** (aplicado en `9669e94`): `runner_service.py` añade UUID
hex(8) al `client_id` configurado, eliminando colisiones. Verificar que
está vigente:

```bash
docker logs captia-bms-mosquitto --since 30s | grep -oE 'as captia-bms-[^ ]+' | sort -u
# Debería mostrar 1 cliente único por job, no docenas con el mismo ID.
```

**Recovery manual**: matar procesos host zombies + reiniciar container generator.

## Notebooks fallan al importar `notebooks._common`

Asegúrate de ejecutar Jupyter desde la raíz del repo:

```bash
cd /path/to/captia-synthetic-data-bms        # raíz del repo
uv run --with jupyterlab jupyter lab notebooks/
```

El kernel debe ser **Python 3.12** del entorno `.venv` del repo.

## InfluxDB devuelve 401

Token caducado o tipo incorrecto. Regenerar con:

```bash
openssl rand -hex 32
```

Y actualizar `INFLUXDB_TOKEN` en `.env`.

## Notebooks `needs-stack` muestran datos vacíos

Verifica que el stack esté corriendo (`task up` o `make demo`) y que la
ingesta haya generado puntos:

```bash
task smoke
# o
scripts/smoke_influx.sh
```

## Generador no publica MQTT

```bash
curl -s http://localhost:8121/healthz
curl -X POST http://localhost:8121/v1/control/start \
  -H "Authorization: Bearer $BMS_API_TOKEN" \
  -d '{"mode":"live","aulas":10}'
```

## `mkdocs serve` falla

```bash
uv run --with mkdocs-material mkdocs serve --dev-addr 0.0.0.0:8000
```

Si el port 8000 está ocupado, cambia `--dev-addr`.

## CSV mock no existe

Re-genera:

```bash
uv run python scripts/build_notebook_data.py
```
