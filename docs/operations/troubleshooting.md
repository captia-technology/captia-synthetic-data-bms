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

## Notebooks fallan al importar `notebooks._common`

Asegúrate de ejecutar Jupyter desde la raíz del repo:

```bash
cd C:\CAPTIA\CAPTIA-SYNTHETIC-DATA-BMS
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
