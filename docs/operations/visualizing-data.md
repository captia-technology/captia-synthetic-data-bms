# Configurar y visualizar datos

Guía operativa única para **levantar el stack** y **ver los datos por todos los frontales** disponibles: Grafana, MQTTX-Web, InfluxDB UI, Prometheus, Loki.

> **Audiencia**: alguien que ya clonó el repo y tiene Docker funcionando. Si vienes desde cero, pasa primero por [QUICKSTART](../QUICKSTART.md).

---

## 0. Configurar antes de visualizar

### 0.1 Variables de entorno

```powershell
copy .env.example .env
```

Edita `.env` solo si quieres cambiar algo. Las que más importan para la visualización:

| Variable | Default | Para qué |
|----------|---------|----------|
| `MQTT_PORT_HOST` | `1884` | Puerto host del broker MQTT (TCP) |
| `MQTT_WS_PORT_HOST` | `9102` | WebSocket — lo usa MQTTX-Web |
| `INFLUXDB_PORT_HOST` | `8087` | UI de InfluxDB |
| `GRAFANA_PORT_HOST` | `3001` | UI de Grafana |
| `MQTTX_WEB_PORT_HOST` | `8083` | UI de MQTTX-Web |
| `PROMETHEUS_PORT_HOST` | `9090` | UI de Prometheus |
| `LOKI_PORT_HOST` | `3100` | API de Loki (consultable desde Grafana) |
| `BMS_GENERATOR_PORT_HOST` | `8121` | API + `/metrics` del generator |
| `BMS_N_AULAS` | `10` | Aulas a simular |
| `BMS_FAULTS_ENABLED` | `false` | Inyectar averías HVAC |

`INFLUXDB_TOKEN` y `BMS_API_TOKEN` se generan vacíos: ponlos con
```powershell
openssl rand -hex 32
```

### 0.2 Levantar todo

```powershell
make quickstart        # primer arranque: rellena .env y arranca todo
# o, si ya tienes .env:
make up                # levanta sin demo
make demo              # levanta + publica datos sintéticos en bucle
```

Verifica:

```powershell
make ps                # estado de contenedores
make smoke             # healthchecks + verify schema
```

Esperado: 10 contenedores `Up (healthy)` en menos de 60 s.

---

## 1. Visualizar en Grafana (la vía principal)

**URL**: <http://localhost:3001>
**Login**: `admin` / `admin` (cámbialo en `.env` para producción)

Los dashboards se provisionan automáticamente desde `infra/grafana/dashboards/`. Cuatro paneles, cada uno orientado a un caso de uso:

| Dashboard | UID | Para qué |
|-----------|-----|----------|
| **System Health Cockpit** | [`bms-overview`](http://localhost:3001/d/bms-overview) | Estado del pipeline: ingest rate, freshness, healthchecks, cardinality |
| **Energy Analytics (Caso B)** | [`bms-consumption-b`](http://localhost:3001/d/bms-consumption-b) | kWh hoy, top-10 aulas consumidoras, correlación T_outdoor ↔ power, load profile diario |
| **Fault Detection (Caso C)** | [`bms-faults-c`](http://localhost:3001/d/bms-faults-c) | Faults activos, MTBF, distribución por tipo, severity, timeline |
| **Air Quality & Comfort (Caso D)** | [`bms-iaq-d`](http://localhost:3001/d/bms-iaq-d) | CO₂ por aula con thresholds WHO/ASHRAE, humidity, ruido, IAQ index |

### Si los dashboards salen vacíos
1. Confirma que el generator está publicando: `docker logs captia-bms-generator --tail 20`.
2. Confirma que Telegraf escribe: `docker logs captia-bms-telegraf --tail 20` debe mostrar `wrote N metrics to influxdb`.
3. Si no, ver [TROUBLESHOOTING](../TROUBLESHOOTING.md).

### Recargar dashboards tras editar JSON
```powershell
docker exec captia-bms-grafana sh -c 'kill -HUP 1'
```

---

## 2. Ver tráfico MQTT crudo (MQTTX-Web)

**URL**: <http://localhost:8083>

Cliente MQTT con UI servida en navegador. Conecta vía WebSocket al broker y muestra cada mensaje con su topic, QoS, retain y payload.

### Importar conexión + suscripciones predefinidas (1 click)

1. Descarga (o accede directamente desde el contenedor): <http://localhost:8083/captia-bms-mqttx-config.json>
2. En la UI: **⚙️ Settings → Data → Import Data**, sube el JSON.
3. Aparecerá la conexión **`CAPTIA BMS · local (WebSocket)`** con 7 suscripciones (`captia/#`, telemetría, temperature, co2, power, iaq, events).
4. Click la conexión → **Connect**.

Detalle completo en [`infra/mqttx/README.md`](../../infra/mqttx/README.md).

### Si prefieres CLI sin abrir navegador

```powershell
# Firehose
docker exec captia-bms-mosquitto mosquitto_sub -h localhost -p 1883 -t "captia/#" -v

# Solo CO2
docker exec captia-bms-mosquitto mosquitto_sub -h localhost -p 1883 `
  -t "captia/dev/bms_classrooms/ies_simarro/+/telemetry/co2" -v
```

### Schema del payload

```json
{ "value": 23.45, "ts_ns": 1778424694000000000 }
```

Topic: `captia/{env}/{tenant}/{site}/{device}/{stream}/{name}`
Ejemplo: `captia/dev/bms_classrooms/ies_simarro/AULA01/telemetry/temperature_01`

Variables disponibles (telemetría continua, sample real):
`avg-sound-level`, `co2`, `iaq-index`, `luminosity`, `occupancy`, `people-count`, `relative-humidity`, `temperature_01`, `power_01`, `temperature-outdoor`.

---

## 3. Consultar InfluxDB directamente (Flux)

**URL**: <http://localhost:8087>
**Login**: `admin` / lo que pusieras en `INFLUXDB_ADMIN_PASSWORD`

### Buckets y retención

| Bucket | Retención | Origen |
|--------|-----------|--------|
| `telemetry` | 14 d | raw del generator vía Telegraf |
| `telemetry_1m` | 30 d | rollup automático (Flux task) |
| `telemetry_15m` | 90 d | rollup |
| `telemetry_1h` | 365 d | rollup |
| `state_events` | 90 d | eventos discretos (HVAC on/off, faults) |
| `telemetry_events` | 90 d | eventos puntuales (`event/*` topics) |
| `captia_metadata` | ∞ | catálogo de variables |

### Queries Flux útiles

**Última temperatura por aula (5 min)**
```flux
from(bucket: "telemetry")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "captia_point" and r.variable == "temperature_01")
  |> last()
  |> keep(columns: ["asset_id", "_value", "_time"])
```

**Top-5 aulas por consumo 24h**
```flux
from(bucket: "telemetry")
  |> range(start: -24h)
  |> filter(fn: (r) => r._measurement == "captia_point" and r.variable == "power_01")
  |> aggregateWindow(every: 5m, fn: mean, createEmpty: false)
  |> map(fn: (r) => ({ r with _value: r._value * (5.0 / 60.0) / 1000.0 }))
  |> group(columns: ["asset_id"])
  |> sum()
  |> group()
  |> sort(columns: ["_value"], desc: true)
  |> limit(n: 5)
```

**Eventos de avería en últimos 7 días**
```flux
from(bucket: "state_events")
  |> range(start: -7d)
  |> filter(fn: (r) => r._measurement == "captia_point_state" and r.variable =~ /^fault\./)
  |> filter(fn: (r) => r._value > 0.0)
```

Pega cualquiera en **Data Explorer** → switch a **Script Editor**.

---

## 4. Métricas del generator (Prometheus)

**URL UI Prometheus**: <http://localhost:9090>
**URL raw del generator**: <http://localhost:8121/metrics>

Métricas expuestas con prefijo `captia_bms_*`:

| Métrica | Tipo | Para qué |
|---------|------|----------|
| `captia_bms_messages_published_total` | counter | Total publicados a MQTT |
| `captia_bms_publish_errors_total{reason}` | counter | Errores de publicación, etiquetados por causa |
| `captia_bms_points_generated_total` | counter | DataPoints producidos antes de filtros |
| `captia_bms_faults_injected_total{type}` | counter | Faults inyectados por tipo |
| `captia_bms_uptime_seconds` | gauge | Uptime del proceso |
| `captia_bms_connected` | gauge | 1 si conectado al broker |
| `captia_bms_active_jobs` | gauge | Jobs activos (dump/live) |
| `captia_bms_dump_export_seconds_total` | counter | Tiempo acumulado en exports |

Queries PromQL de referencia (pega en `:9090/graph`):

```promql
# Publish rate (msg/s, ventana 5m)
rate(captia_bms_messages_published_total[5m])

# Tasa de errores por causa
sum by (reason) (rate(captia_bms_publish_errors_total[5m]))

# ¿Está conectado el generator?
captia_bms_connected
```

---

## 5. Logs centralizados (Loki vía Grafana)

Promtail recolecta los stdout/stderr de todos los contenedores y los envía a Loki. Se consultan desde Grafana.

1. Grafana → **Explore** (icono brújula).
2. Datasource: **Loki**.
3. Query LogQL típico:
   ```logql
   {container="captia-bms-generator"} |= "ERROR"
   {container=~"captia-bms-.*"} | json | line_format "{{.level}} {{.message}}"
   ```

---

## 6. Verificación end-to-end (smoke test)

Sin abrir UI:

```powershell
make smoke              # healthchecks + verify-canonical-schema
make verify:influx      # 6 buckets esperados + tags presentes
make verify:mqtt        # publish + subscribe round-trip
```

Si los 3 pasan, **el pipeline está sano** y todas las UIs deberían mostrar datos.

---

## 7. Mapa de URLs y credenciales

| Servicio | URL | Login |
|----------|-----|-------|
| Grafana | <http://localhost:3001> | `admin` / `admin` |
| MQTTX-Web | <http://localhost:8083> | — |
| InfluxDB UI | <http://localhost:8087> | `admin` / `INFLUXDB_ADMIN_PASSWORD` |
| Prometheus | <http://localhost:9090> | — |
| Generator API | <http://localhost:8121/docs> | `Bearer BMS_API_TOKEN` |
| Generator metrics | <http://localhost:8121/metrics> | — |
| Mosquitto MQTT | `tcp://localhost:1884` | anónimo (dev) |
| Mosquitto WS | `ws://localhost:9102/mqtt` | anónimo (dev) |

---

## Ver también

- [QUICKSTART](../QUICKSTART.md) — primer arranque en 5 min.
- [TROUBLESHOOTING](../TROUBLESHOOTING.md) — qué hacer cuando algo no muestra datos.
- [`infra/mqttx/README.md`](../../infra/mqttx/README.md) — detalle de MQTTX-Web.
- [`docs/specs/synthetic-bms/05-observability-spec.md`](../specs/synthetic-bms/05-observability-spec.md) — diseño de la observabilidad.
- [`docs/architecture/data-flow.md`](../architecture/data-flow.md) — flujo MQTT → Telegraf → InfluxDB → Grafana.
