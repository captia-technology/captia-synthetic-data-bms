# Empezar

> **Última verificación:** 2026-05-10
> **Audiencia:** primer contacto con el repo. Si ya levantaste el stack, salta a [Modelo físico](../physical-model/index.md) o [Auditoría](../audit/STATUS.md).

## Pre-requisitos

- **Docker Desktop** ≥ 20.10 con `docker compose` v2.
- **uv** ≥ 0.5 (`pipx install uv` o [docs.astral.sh/uv](https://docs.astral.sh/uv/)).
- **Python** ≥ 3.12.
- **Make** (Linux/Mac nativo, Windows vía Git Bash o WSL).
- 6 GB RAM libres y ~3 GB de disco para volúmenes Docker.

## Camino más rápido

```bash
git clone https://github.com/captiatechnology/CAPTIA-SYNTHETIC-DATA-BMS
cd CAPTIA-SYNTHETIC-DATA-BMS
cp .env.example .env
# Editar .env: poner BMS_API_TOKEN, INFLUXDB_TOKEN, INFLUXDB_ADMIN_PASSWORD
make demo
```

Tras `make demo`:

- 8 servicios `healthy` (verificar con `docker compose ps`).
- Generador FastAPI escuchando en `http://localhost:8120`.
- Grafana en `http://localhost:3001` con 4 datasources y 4 dashboards provisionados.
- InfluxDB en `http://localhost:8087` con 7 buckets y 5 tareas Flux activas.

Ver [Quickstart](../QUICKSTART.md) para el flujo completo y [Troubleshooting](../TROUBLESHOOTING.md) si algo no levanta.

## Siguiente paso

| Si quieres… | Ve a |
|---|---|
| Entender qué hace cada servicio | [Arquitectura — Visión general](../architecture/index.md) |
| Saber por qué los datos son creíbles físicamente | [Modelo físico — Resumen](../physical-model/index.md) |
| Comparar la implementación con CAPTIA-connect | [Auditoría — Consistencia](../audit/CONSISTENCY_MATRIX.md) |
| Auditar los hallazgos top 20 | [Auditoría — Reporte](../audit/AUDIT_REPORT.md) |
