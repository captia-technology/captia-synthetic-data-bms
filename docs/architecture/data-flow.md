# Flujo de un dato — del sensor a Grafana

> **Última verificación:** 2026-05-10

Recorrido de un único punto de telemetría desde el sensor BMS de AULA01
hasta su visualización en Grafana.

## Escenario

El sensor de CO₂ de AULA01 mide 712 ppm a las 08:05:45 UTC del 2026-05-10.

## Paso 1 — el sensor publica

```
Topic:   captia/dev/default/ies_simarro/AULA01/telemetry/co2
Payload: {"value": 712, "ts_ns": 1714572345000000000}
```

QoS 1. El sensor no espera más allá del ACK del broker.

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

- **`ac_state` (on-change)**: salta paso 5 (no rollup); va directamente a
  `state_events` con dedup.
- **Eventos del sistema**: topic `event/{name}` → bucket
  `telemetry_events`.
- **Etiquetas de fallo Caso C**: measurement separado `captia_fault_labels`
  en `state_events`.

## Latencia

- Sensor → broker: ~5 ms.
- Broker → Telegraf: ~2 ms.
- Telegraf → Influx: ~8 ms.
- Influx → Grafana: ~50 ms (con cache Redis).

Total mediana: **~65 ms**. Ver `docs/audit/E2E_VALIDATION_REPORT.md`.

## Ejecutar este flujo

- [Quickstart](../QUICKSTART.md) levanta los 8 servicios.
- [`notebooks/01_case_A_pipeline_iot/02_publicacion_mqtt_a_influxdb.ipynb`](https://github.com/captia-technology/CAPTIA-SYNTHETIC-DATA-BMS/blob/main/notebooks/01_case_A_pipeline_iot/02_publicacion_mqtt_a_influxdb.ipynb)
  reproduce paso 1 en clase.
- [`notebooks/01_case_A_pipeline_iot/03_validacion_telegraf_influx_grafana.ipynb`](https://github.com/captia-technology/CAPTIA-SYNTHETIC-DATA-BMS/blob/main/notebooks/01_case_A_pipeline_iot/03_validacion_telegraf_influx_grafana.ipynb)
  comprueba pasos 4–6.
