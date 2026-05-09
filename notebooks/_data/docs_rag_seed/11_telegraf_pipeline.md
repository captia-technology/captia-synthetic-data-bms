# Pipeline Telegraf — Mosquitto a InfluxDB

Telegraf es el agente que conecta Mosquitto con InfluxDB en CENTINELA+.
Configuración mínima:

```toml
[[inputs.mqtt_consumer]]
  servers = ["tcp://mosquitto:1883"]
  topics = ["captia/+/+/+/+/telemetry/+"]
  name_override = "captia_point"
  data_format = "json"

[[processors.regex]]
  [[processors.regex.tags]]
    key = "topic"
    pattern = "captia/([^/]+)/([^/]+)/([^/]+)/([^/]+)/[^/]+/([^/]+)"
    replacement = "${1}"
    result_key = "captia_env"

[[outputs.influxdb_v2]]
  urls = ["http://influxdb:8086"]
  token = "$INFLUXDB_TOKEN"
  organization = "captia"
  bucket = "telemetry"
  fieldpass = ["value"]
```

Observaciones:

- `fieldpass = ["value"]` descarta cualquier otro campo del payload JSON.
- `name_override = "captia_point"` fuerza el measurement único.
- Las señales `_state` se enrutan a `state_events` mediante
  `processors.clone` + `processors.dedup`.
