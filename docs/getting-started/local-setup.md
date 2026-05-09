# Setup local

> **Última verificación:** 2026-05-10
> **Camino más rápido:** [Quickstart](../QUICKSTART.md).

## Pre-requisitos

| Herramienta | Versión | Notas |
|---|---|---|
| Docker Desktop | ≥ 20.10 | Compose v2 |
| `uv` | ≥ 0.5 | Gestión Python |
| Python | ≥ 3.12 | Provisto por `uv sync` |
| Make | nativo Linux/Mac | Windows: Git Bash o WSL |
| RAM libre | 6 GB | Stack completo |
| Disco | 3 GB | Volúmenes Docker |

## Pasos

```bash
# 1. Clonar el repo
git clone https://github.com/captiatechnology/CAPTIA-SYNTHETIC-DATA-BMS
cd CAPTIA-SYNTHETIC-DATA-BMS

# 2. Sincronizar dependencias (workspace uv)
uv sync --all-extras

# 3. Variables de entorno
cp .env.example .env
# Genera tokens reales:
sed -i 's/CHANGE_ME_USE_OPENSSL_RAND/'$(openssl rand -hex 32)'/g' .env

# 4. Levantar el stack
make demo
# o equivalentemente:
task up

# 5. Probar
task smoke
```

## Verificación

```bash
docker compose ps
# 8 servicios deben aparecer (healthy)

curl -s http://localhost:8121/healthz
# {"status": "ok"}

curl -s http://localhost:8087/health
# {"status":"pass", ...}

curl -s http://localhost:3001/api/health
# {"database": "ok", ...}
```

## Generar datos sintéticos

```bash
# Modo live (publica MQTT continuamente)
curl -X POST http://localhost:8121/v1/control/start \
  -H "Authorization: Bearer $BMS_API_TOKEN" \
  -d '{"mode":"live","aulas":10}'

# Backfill 12 meses → fichero .lp
curl -X POST http://localhost:8121/v1/datasets/export \
  -H "Authorization: Bearer $BMS_API_TOKEN" \
  -d '{"months":12,"format":"line_protocol"}'

# Detener
curl -X POST http://localhost:8121/v1/control/stop \
  -H "Authorization: Bearer $BMS_API_TOKEN"
```

## Generar mocks para notebooks

```bash
uv run python scripts/build_notebook_data.py
# Crea ~80 MB de CSV en notebooks/_data/
```

## Acceso a interfaces

| URL | Servicio | Credenciales |
|---|---|---|
| `http://localhost:3001` | Grafana | admin / `$GRAFANA_ADMIN_PASSWORD` |
| `http://localhost:8087` | InfluxDB UI | admin / `$INFLUXDB_ADMIN_PASSWORD` |
| `http://localhost:8121/docs` | FastAPI Swagger | bearer `$BMS_API_TOKEN` |
| `http://localhost:9090` | Prometheus | sin auth (local) |
| `http://localhost:3100` | Loki API | sin auth (local) |

## Apagar

```bash
make down            # detiene contenedores, conserva volúmenes
make down-clean      # también borra volúmenes (¡pierdes datos!)
```
