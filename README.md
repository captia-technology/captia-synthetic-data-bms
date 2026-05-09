# CAPTIA-SYNTHETIC-DATA-BMS

Microservicio generador de datos sintéticos **BMS (Building Management System)** para CAPTIA Technology.

Diseñado para soportar 11 casos de uso educativos del IES Simarro: pipeline IoT en vivo, predicción de consumo eléctrico, detección de anomalías HVAC y modelado de calidad de aire / ocupación.

> Identifier nota: BMS = Building Management System (aulas educativas), NO Battery Management System.

## Arquitectura

```
USER ──HTTP(8120)──▶ bms-data-generator (FastAPI)
                          │  vendor.synthetic_generator (hexagonal)
                          ▼  + extensions.bms_calibration
                     mosquitto :1884 ──▶ telegraf ──▶ influxdb :8087
                                                          │
                       redis :6379 ◀──── grafana :3001 ◀──┘
                                              ▲
                       prometheus :9090 ──────┤
                       loki :3100 ◀── promtail
```

Componentes:

- **`vendor/synthetic-generator/`** — generador hexagonal vendorizado de CAPTIA-CONNECT (read-only).
- **`extensions/bms_calibration/`** — calibración local + injection de 4 tipos de fallos HVAC.
- **`modules/bms-data-generator/`** — control plane FastAPI.
- **`compose/`** — stack Docker (mosquitto, telegraf, influxdb, redis, grafana, prometheus, loki, promtail).
- **`docs/specs/synthetic-bms/`** — paquete SDD (specs + ADRs + plan).

Detalles en `docs/specs/synthetic-bms/03-architecture-spec.md`.

## Quickstart

### 1. Prerequisitos

- Docker 24+, Docker Compose v2.
- Python 3.12+, [`uv`](https://github.com/astral-sh/uv).
- [`task`](https://taskfile.dev) (Taskfile runner).

### 2. Configuración

```bash
cp .env.example .env
# Generar secretos:
echo "INFLUXDB_TOKEN=$(openssl rand -hex 32)" >> .env
echo "INFLUXDB_ADMIN_PASSWORD=$(openssl rand -hex 16)" >> .env
echo "BMS_API_TOKEN=$(openssl rand -hex 32)" >> .env
```

Edita `.env` para sobrescribir defaults si fuera necesario.

### 3. Instalar dependencias Python

```bash
uv sync
```

### 4. Levantar el stack

```bash
task up
task wait:healthy   # Espera healthchecks (max 120 s)
task ps             # Ver estado
```

### 5. Verificar

```bash
task smoke          # MQTT publish, Influx query, Grafana healthz, schema canónico
```

Abre Grafana: http://localhost:3001 (`admin` / `admin` por defecto).

### 6. Casos de uso

| Caso | Comando | Descripción |
|------|---------|-------------|
| A — Pipeline IoT en vivo | `curl -X POST http://localhost:8120/v1/control/start ...` | Generador → MQTT → Telegraf → InfluxDB → Grafana en tiempo real |
| B — Backfill consumo 12m | `task dump:caseB` | Dataset 12 meses para SARIMA / XGBoost / LSTM |
| C — Fallos HVAC 6m | `task dump:caseC` | Backfill con fallos etiquetados para Isolation Forest / Autoencoder |
| D — IAQ 1min 3m | `task dump:caseD` | Calidad aire / ocupación para modelo CO2 → ocupancia |

## Reglas de oro

1. **Spec-driven**: leer `docs/specs/synthetic-bms/` antes de modificar.
2. **Schema canónico CAPTIA inviolable** (`captia_point` + 5 tags).
3. **Vendor read-only** (`vendor/synthetic-generator/`).
4. **Determinismo**: `seed=42`, `numpy.random.default_rng`.
5. **Sin secretos en código**.

Detalle: `.claude/rules/`.

## Stack y versiones

| Servicio | Versión | Puerto host |
|----------|---------|-------------|
| Mosquitto | `eclipse-mosquitto:2.0.18` | 1884 (MQTT), 9002 (WS) |
| InfluxDB | `influxdb:2.7` | 8087 |
| Redis | `redis:7-alpine` | (interno 6379) |
| Telegraf | `telegraf:1.32` | (interno 9273 metrics) |
| Grafana | `grafana/grafana:11.4.0` (build local) | 3001 |
| Prometheus | `prom/prometheus:v2.49.1` | 9090 |
| Loki | `grafana/loki:2.9.4` | 3100 |
| Promtail | `grafana/promtail:2.9.4` | (sin puerto host) |
| BMS Generator | Python 3.12, FastAPI, Uvicorn | 8120 |

## Comandos task

```bash
task --list              # Ver todos los targets
task install             # uv sync
task lint                # ruff check + format check
task test                # pytest unit
task test:integration    # pytest integration
task up                  # Levantar stack
task down                # Detener (volúmenes preservados)
task clean               # Detener Y borrar volúmenes
task smoke               # All smoke checks
task dump:caseB          # Generar dump Caso B
task config:render       # Ver compose merged
```

## Documentación

- Specs SDD: `docs/specs/synthetic-bms/`.
- Casos de uso CAPTIA: `docs/CAPTIA_Informe_CasosDeUso_DatosSinteticos.md`.
- Schema canónico CENTINELA+: `docs/CENTINELA_Guia_Alumnos_v4.md`.
- Arquitectura medallion: `docs/MEDALLION_Arquitectura_Guia_Referencia.md`.

## Licencia

Proprietary — CAPTIA Technology.

## Soporte

- Issues: en este repo.
- Contacto: tech@captiatechnology.com.
