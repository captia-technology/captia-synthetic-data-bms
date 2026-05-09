# ¿Qué es CENTINELA+?

CENTINELA+ es la plataforma de monitorización de edificios desarrollada por
CAPTIA Technology. Recoge telemetría de sensores BMS (Building Management
System) en aulas educativas, normaliza los datos al schema canónico
`captia_point` y los expone vía dashboards Grafana, agentes y API.

Componentes clave:

- **Mosquitto** — broker MQTT donde publican los sensores en topics
  jerárquicos `captia/{env}/{tenant}/{site}/{device}/telemetry/{name}`.
- **Telegraf** — agente que parsea topics, extrae 5 tags canónicos y
  escribe en InfluxDB.
- **InfluxDB 2.7** — base de datos de series temporales con 7 buckets
  (`telemetry`, rollups `_1m/_15m/_1h`, `state_events`, `telemetry_events`,
  `captia_metadata`).
- **Grafana 11** — dashboards en vivo.
- **Dashboard Adapter** — API REST que cachea consultas en Redis.

Diseño: separar sensor (solo MQTT) de almacenamiento (Telegraf + Influx)
para poder evolucionar cualquier capa sin romper la otra.
