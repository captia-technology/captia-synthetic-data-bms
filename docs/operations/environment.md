# Variables de entorno y secretos

> **Última verificación:** 2026-05-10
> **Plantilla:** [`.env.example`](https://github.com/captiatechnology/CAPTIA-SYNTHETIC-DATA-BMS/blob/main/.env.example).

## Reglas

1. **Nunca commitear `.env`.** Está en `.gitignore`.
2. **Secretos con `CHANGE_ME`** en `.env.example`. Regenerar con:
   ```bash
   openssl rand -hex 32
   ```
3. **Defaults locales** son solo para desarrollo (ej. token
   `simarro-dev-token-2026`); no usar en producción.
4. **Notebooks leen `.env` con `notebooks._common.connection.load_env`.**

## Variables clave

### Compose

| Variable | Default | Uso |
|---|---|---|
| `ENVIRONMENT` | `development` | Lee `bms-data-generator`. |
| `LOG_LEVEL` | `INFO` | Nivel logger Python / Telegraf. |
| `CAPTIA_NETWORK_NAME` | `captia-bms-network` | Red Docker. |

### MQTT (Mosquitto)

| Variable | Default | Uso |
|---|---|---|
| `MQTT_HOST` | `mosquitto` | Hostname interno Docker. |
| `MQTT_PORT_HOST` | `1884` | Puerto host. |
| `MQTT_WS_PORT_HOST` | `9102` | WebSocket host. |
| `CAPTIA_TOPIC_PREFIX` | `captia` | Constante del topic. |
| `CAPTIA_ENV` | `dev` | Tag `captia_env`. |
| `CAPTIA_TENANT` | `default` | Nivel del topic. |
| `CAPTIA_SITE` | `ies_simarro` | Tag `site_id`. |
| `CAPTIA_MQTT_QOS` | `1` | QoS publish. |

### InfluxDB

| Variable | Default | Uso |
|---|---|---|
| `INFLUXDB_URL` | `http://influxdb:8086` | URL interna stack. |
| `INFLUXDB_PORT_HOST` | `8087` | Puerto host. |
| `INFLUXDB_ORG` | `captia` | Org. |
| `INFLUXDB_BUCKET` | `telemetry` | Bucket por defecto. |
| `INFLUXDB_TOKEN` | `CHANGE_ME...` | Admin token. **Regenerar.** |
| `INFLUXDB_ADMIN_USER` | `admin` | Usuario admin. |
| `INFLUXDB_ADMIN_PASSWORD` | `CHANGE_ME...` | Password admin. |
| `INFLUX_OFFLINE` | (ausente) | Si `true`, los notebooks usan mocks. |

### Generador BMS

| Variable | Default | Uso |
|---|---|---|
| `BMS_GENERATOR_PORT_HOST` | `8121` | Puerto host. |
| `BMS_DOMAIN_ID` | `bms_classrooms` | Tag `domain_id`. |
| `BMS_N_AULAS` | `10` | Cuántas aulas. |
| `BMS_SEED` | `42` | Determinismo. |
| `BMS_BACKFILL_DEFAULT_DAYS` | `30` | Backfill default. |
| `BMS_FAULTS_ENABLED` | `false` | Activa Caso C. |
| `BMS_API_TOKEN` | `CHANGE_ME...` | Bearer API. **Regenerar.** |

### Observabilidad

| Variable | Default | Uso |
|---|---|---|
| `PROMETHEUS_PORT_HOST` | `9090` | Puerto host. |
| `LOKI_PORT_HOST` | `3100` | Puerto host. |
| `LOKI_URL` | `http://loki:3100` | URL interna stack. |
| `GRAFANA_PORT_HOST` | `3001` | Puerto host. |

## Plantillas

### Local desarrollo

```bash
cp .env.example .env
sed -i 's/CHANGE_ME_USE_OPENSSL_RAND/'$(openssl rand -hex 32)'/g' .env
```

### Producción (esquema)

```bash
INFLUXDB_URL=https://<your-influxdb-host>     # ej. https://influx.<tu-tenant>.example.com
INFLUXDB_TOKEN=<your-influxdb-token>          # gestionar vía secret manager
INFLUXDB_ORG=<your-org>
CAPTIA_ENV=prod
CAPTIA_SITE=<your-site-id>
```

> Las URL y tokens de cualquier despliegue real (ej. el del piloto IES Simarro)
> se gestionan en el secret manager corporativo y **no** se commitean al repo.
