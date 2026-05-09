# Topics MQTT CAPTIA

Los topics MQTT son jerárquicos para que Mosquitto pueda aplicar ACLs por
nivel y para que Telegraf pueda extraer los 5 tags con una sola regex.

Estructura general:

- Telemetría: `captia/{env}/{tenant}/{site}/{device}/telemetry/{variable}`
- Eventos: `captia/{env}/{tenant}/{site}/{device}/event/{variable}`

Reglas:

- 6 niveles fijos (no 5, no 7).
- `env` ∈ {dev, staging, prod}.
- `tenant` típicamente `default` salvo multi-tenancy explícita.
- `device` mapea a `asset_id` (p.ej. `AULA01`).
- `variable` usa underscore (`co2`, `temperature_01`, `t_voc`).

QoS recomendado: 1 (al menos una entrega). El sensor no espera ACK más
allá del propio QoS — Telegraf, no el sensor, es responsable de
persistencia.
