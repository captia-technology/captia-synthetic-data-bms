# Regla 004 — Convenciones Docker Compose

## Obligatorio

- Tags fijos (ej. `eclipse-mosquitto:2.0.18`, `influxdb:2.7`, `redis:7-alpine`, `telegraf:1.32`).
- Healthcheck en cada servicio persistente.
- `${VAR:-default}` para variables expuestas en `.env.example`.
- `depends_on: condition: service_healthy` para consumidores.
- Red `captia-network` (declarada en `compose/base.yaml`).
- Volúmenes nombrados (no anonymous mounts).
- `restart: unless-stopped` salvo en jobs one-shot (`restart: "no"`).
- Limits: `mem_limit`, `cpus` documentados en services.
- Container name con prefijo `captia-bms-*`.

## Prohibido

- `image: foo:latest`.
- `password: hardcoded`.
- `network_mode: host`.
- Secretos en `command:` o `environment:` literal.
