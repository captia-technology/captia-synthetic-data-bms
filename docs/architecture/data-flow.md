# Flujo de un dato — del sensor a Grafana

> **Última verificación:** 2026-05-10

Recorrido de un único punto de telemetría desde el sensor BMS de AULA01
hasta su visualización en Grafana.

## Pre-requisito — bootstrap del catálogo

Antes de cualquier flujo de telemetría, en el primer arranque (y en cada
deploy) el servicio one-shot `metadata-bootstrap`
(`tools/metadata-bootstrap/bootstrap.py`, encadenado tras `influx-init`
en `compose/data-plane-init.yaml`) puebla el bucket `captia_metadata`
con `N_aulas × 33 vars` entries (21 vendor + 12 derivadas) más 1
`captia_domain_meta`. Esto permite a dashboards y queries Flux
correlacionar telemetría con `display_name`, `unit`, `range_min/max`,
`category`, `metric_kind` y `storage_mode` mediante JOIN por los tags
compartidos `domain_id, site_id, variable, captia_env`.

## Escenario

El sensor de CO₂ de AULA01 mide 712 ppm a las 08:05:45 UTC del 2026-05-10.

## Paso 1 — el generator publica

El `bms-data-generator` ejecuta su loop interno (vendor `ScenarioRunner`),
genera DataPoints físicos y los pasa al `AliasSinkAdapter`. Antes de
publicar al broker, el adapter:

1. **Deriva** 0+ DataPoints adicionales según `derivations.yaml` (ej.
   `co2 → t-voc`, `temperature → temperature-indoor`).
2. **Renombra** vendor → production_name según `variables.yaml` (ej.
   `humidity → relative-humidity`).

Cada DataPoint se publica vía paho-mqtt al broker con QoS 1:

```
Topic:   captia/dev/default/ies_simarro/AULA01/telemetry/co2
Payload: {"value": 712, "ts_ns": 1714572345000000000}
```

El sensor real (en producción) sigue el mismo formato (drop-in replacement).

## Paso 2 — Mosquitto enruta

`mqtt_consumer` de Telegraf está suscrito a
`captia/+/+/+/+/telemetry/+`. El topic coincide.

## Paso 3 — Telegraf parsea

`processors.regex` extrae los 5 tags del topic:

```
captia_env  = dev
domain_id   = (configurado en Telegraf)  → bms_classrooms
site_id     = ies_simarro
asset_id    = AULA01
variable    = co2
```

`processors.json` extrae `value` y `ts_ns` del payload. `co2` no termina en
`_state` → señal continua → bucket `telemetry`.

## Paso 4 — Telegraf escribe a InfluxDB

```
captia_point,captia_env=dev,domain_id=bms_classrooms,site_id=ies_simarro,asset_id=AULA01,variable=co2 value=712 1714572345000000000
```

## Paso 5 — Tareas Flux downsample

Cada minuto, una tarea Flux agrega `mean`, `min`, `max` para señales
`analog_gauge` y emite a `telemetry_1m` con un tag adicional `stat`:

```
captia_point,...,variable=co2,stat=mean  value=708.5  1714572360000000000
captia_point,...,variable=co2,stat=min   value=695.0  ...
captia_point,...,variable=co2,stat=max   value=721.0  ...
```

A las 15 min se vuelve a agregar a `telemetry_15m` y a la hora a
`telemetry_1h`.

## Paso 6 — Grafana consulta

Un dashboard ejecuta:

```python
from(bucket: "telemetry_1m")
  |> range(start: -1h)
  |> filter(fn: (r) => r.asset_id == "AULA01")
  |> filter(fn: (r) => r.variable == "co2")
  |> filter(fn: (r) => r.stat == "mean")
```

El Dashboard Adapter cachea esta query en Redis para evitar hits repetidos
durante el período de auto-refresh.

## Paso 7 — Render

Grafana muestra la curva CO₂ AULA01 en tiempo real.

## Variantes

- **`ac_state` (on-change)**: salta paso 5 (no rollup); el processor
  `processors.clone` de Telegraf duplica el point a measurement
  `captia_point_state` con `stat=last` y va al bucket `state_events`
  vía dedup. Variables on-change incluidas: sufijos `*_state`, `*_sp`,
  `*_setpoint`, `*_cmd`, `*_mode`, `relay_*`, `fault.*`, más explícitas
  `ac_control`, `aire_state`, `valve_control`, `valve_state`,
  `fan_speed_03_state`.
- **Eventos cmd/ack**: topic `event/{name}` → measurement
  `captia_cmd_event` → bucket `telemetry_events`. **Vacío en standalone**
  (sólo poblado por controllers reales tipo `captia-connect` con SCADA).
- **Etiquetas de fallo Caso C**: variables `fault.<tipo>` (4 tipos:
  `sensor_drift`, `valve_stuck`, `fan_failure`, `refrigerant_low`)
  emitidas por `extensions/bms_calibration/FaultEventEmitter` → measurement
  `captia_point` (no separado) → clonadas a `state_events`.
- **Variables derivadas** (12 vars del PPTX simarro-prod): el
  `AliasSinkAdapter` aplica un transform declarativo
  (`passthrough`, `jitter`, `linear`, `bool_to_speed`,
  `bool_to_intensity`, `threshold_to_bool`) sobre el DataPoint vendor y
  emite un point adicional con `variable=<production_name>`. Mismas rutas
  downstream que el original.

## Latencia

- Sensor → broker: ~5 ms.
- Broker → Telegraf: ~2 ms.
- Telegraf → Influx: ~8 ms.
- Influx → Grafana: ~50 ms (con cache Redis).

Total mediana: **~65 ms**. Ver `docs/audit/E2E_VALIDATION_REPORT.md`.

## Ejecutar este flujo

- [Quickstart](../QUICKSTART.md) levanta los 10 servicios + 2 one-shots.
- [`notebooks/01_case_A_pipeline_iot/02_publicacion_mqtt_a_influxdb.ipynb`](https://github.com/captia-technology/CAPTIA-SYNTHETIC-DATA-BMS/blob/main/notebooks/01_case_A_pipeline_iot/02_publicacion_mqtt_a_influxdb.ipynb)
  reproduce paso 1 en clase.
- [`notebooks/01_case_A_pipeline_iot/03_validacion_telegraf_influx_grafana.ipynb`](https://github.com/captia-technology/CAPTIA-SYNTHETIC-DATA-BMS/blob/main/notebooks/01_case_A_pipeline_iot/03_validacion_telegraf_influx_grafana.ipynb)
  comprueba pasos 4–6.
