# Auditoría — Mapa exhaustivo del repo

> Generado por el subagente `repo-cartographer` el 2026-05-09 contra el commit
> en `main` tras `c23e8e4` (`fix(telegraf): tag stat=last on state_events`).

## 1. Árbol de carpetas raíz

| Carpeta | Propósito |
|---------|-----------|
| `.claude/` | Agentes, reglas estables, permisos Claude Code |
| `.github/` | Workflows CI/CD (`ci`, `release`, `security`), templates PR/issue, dependabot |
| `compose/` | 4 Docker Compose (`base`, `generator`, `observability`, `data-plane-init`) |
| `config/` | Escenarios y dominios YAML (`projects/`, `domains/`) |
| `docs/` | 37 archivos: specs SDD, guías, presentaciones, **`audit/` (esta carpeta)** |
| `extensions/` | 2 paquetes Python (`bms_calibration`, `bms_signal_alias`) |
| `infra/` | Configs runtime: Mosquitto, Telegraf, InfluxDB tasks/init, Grafana, Prometheus, Loki, Promtail |
| `modules/` | Microservicio FastAPI `bms-data-generator` |
| `output/` | Volumen runtime (dumps `.lp` / `.csv`) |
| `scripts/` | 11 scripts bash (`init_env`, `preflight`, `smoke_*`, `verify_canonical_schema`, `update_vendor`) |
| `tests/` | 5 archivos workspace-level (E2E + e2e/conftest) |
| `vendor/` | `synthetic-generator` vendorizado (BMS-only tras parche `001-bms-only.patch`) |

## 2. Inventario por área

### 2.1 Generador sintético — `vendor/synthetic-generator/`

- Identidad: `synthetic-generator` 0.1.0; Python ≥ 3.10; deps: numpy, pandas, pydantic, pyyaml, paho-mqtt, tqdm.
- Layout hexagonal: `core/` · `ports/` · `domains/` · `sinks/` + `cli.py`.
- Domains incluidos: **solo `bms_classrooms`** (parche `001-bms-only.patch` removió `industrial_refrigeration` + `discrete_manufacturing`).
- Engine: `runner.py:ScenarioRunner` orquesta backfill + live (`run_live` usa `datetime.now()` línea 196).
- Physics modules: `environment.py`, `occupancy.py`, `indoor.py`, `energy.py`, `actuators.py`.
- Tests vendor: 16 (11 unit + 2 integration + 3 snapshot); fixtures: 3 CSV deterministas seed=42.
- LOC `src/`: ~2 581.

### 2.2 Extensions — `extensions/`

| Paquete | Propósito | Tests |
|---|---|---|
| `bms_calibration` | Calibración por aula, fault injection (4 tipos), school calendar Valencia 25-26, physics overrides, `FaultEventEmitter` (T-PV-22) | 5 + 1 nuevo (test_fault_event_sink) |
| `bms_signal_alias` | `AliasSinkAdapter` que renombra `vendor_name → production_name` antes de emit (T-PV-21) | 1 |

15 archivos Python totales, 8 tests.

### 2.3 Microservicio — `modules/bms-data-generator/`

- pyproject: `bms-data-generator` 0.1.0; Python ≥ 3.12; deps: fastapi, uvicorn, pydantic, prometheus-client, python-json-logger, **httpx (runtime)**, synthetic-generator, bms-calibration.
- Endpoints HTTP:
  - `GET /healthz`, `GET /readyz`, `GET /metrics` (públicos)
  - `POST /v1/control/{start,stop}`, `GET /v1/control/status` (Bearer)
  - `POST /v1/datasets/export`, `GET /v1/datasets/jobs/{id}` (Bearer)
  - **`POST /v1/query` (Dashboard Adapter contract, gap #5)** (Bearer)
- Services: `runner_service`, `dump_service`, `query_service`, `calibration_loader`.
- Dockerfile multi-stage `python:3.12-slim`, USER no-root (uid 10001), HEALTHCHECK `curl /healthz`.
- Tests: 28 (unit + integration; subió 24 con la suite del query service).

### 2.4 Infraestructura — `compose/` + `infra/`

| Compose | Servicios | Volúmenes |
|---|---|---|
| `base.yaml` | mosquitto, influxdb, redis, telegraf, grafana | 5 named |
| `observability.yaml` | prometheus, loki, promtail | 2 named |
| `generator.yaml` | bms-data-generator | — |
| `data-plane-init.yaml` | influx-init (one-shot) | — |

Imágenes pinned (sin `latest`):
`eclipse-mosquitto:2.0.18`, `influxdb:2.7`, `redis:7-alpine`, `telegraf:1.32`,
`grafana/grafana:11.4.0` (build local), `prom/prometheus:v2.49.1`,
`grafana/loki:2.9.4`, `grafana/promtail:2.9.4`, `python:3.12-slim`.

Healthchecks: mosquitto, influxdb, redis, telegraf, grafana, prometheus, loki tienen healthcheck. Promtail no (intencional, sidecar).

`infra/`: `mosquitto/mosquitto.conf`, `telegraf/telegraf.conf`, `influxdb/init/init_buckets_tasks.sh` + 6 `.flux` tasks, `grafana/Dockerfile + provisioning/{datasources,dashboards} + dashboards/*.json`, `prometheus/prometheus.yml + rules/bms_alerts.rules.yml`, `loki/loki-config.yml`, `promtail/promtail-config.yml`.

### 2.5 Configs — `config/`

Scenarios: `bms_v1_demo.yaml`, `bms_v1_caseA_e2e_host.yaml`, `bms_v1_caseB_consumption.yaml`, `bms_v1_caseC_faults.yaml`, `bms_v1_caseD_iaq.yaml`.
Domain: `domains/bms_classrooms/{domain.yaml, variables.yaml, faults.yaml}`.

### 2.6 Scripts — `scripts/`

`_load_env.sh`, `init_env.sh`, `preflight.sh`, `wait_healthy.sh`, `smoke_{mqtt,influx,grafana}.sh`, `export_dump.sh`, `verify_canonical_schema.sh`, `update_vendor.sh`. 11 scripts.

### 2.7 Tests

| Localización | Tests |
|---|---|
| vendor/synthetic-generator/tests | 16 |
| extensions/bms_calibration/tests | 5 |
| extensions/bms_signal_alias/tests | 1 |
| modules/bms-data-generator/tests | 28 (8 unit + 20 integration tras gap #5) |
| tests/ root (e2e) | 5 |

Markers: `unit`, `integration`, `smoke`, `snapshot`, `performance`, `slow`. **Sin `[tool.coverage]`** explícito.

### 2.8 CI — `.github/`

- Workflows: `ci.yml` (lint + test + Docker build + compose validate), `release.yml` (tag `v*`, build+push GHCR + GitHub release), `security.yml` (gitleaks + pip-audit + trivy).
- Templates: `PULL_REQUEST_TEMPLATE.md`, `ISSUE_TEMPLATE/{bug_report,feature_request,config}.yml`.
- `CODEOWNERS` (Jaime Sendra), `dependabot.yml` (pip + actions + docker), `FUNDING.yml`.

### 2.9 Docs — `docs/`

Top-level: `QUICKSTART.md`, `TROUBLESHOOTING.md`, `CAPTIA_Informe_CasosDeUso_DatosSinteticos.md`, `CENTINELA_Guia_Alumnos_v4.md`, `MEDALLION_Arquitectura_Guia_Referencia.md`, 2 `.pptx`.

Carpetas:
- `specs/synthetic-bms/` (14 docs SDD: 00-research/open-questions/repo-map, 01..10, STATUS).
- `specs/digital-twin-bms-physics-validation/` (11 docs: 00..11 + STATUS).
- `audit/` (este informe).

### 2.10 Reglas

`.claude/agents/`: 6 subagentes (`repo-cartographer`, `spec-architect`, `infra-reviewer`, `observability-reviewer`, `qa-reviewer`, `security-reviewer`).
`.claude/rules/`: 5 reglas estables (SDD, schema canónico, vendoring, Compose, idioma). Cambios en reglas requieren ADR.

## 3. Servicios externos en ejecución (snapshot al iniciar audit)

```
captia-bms-grafana    Up 23 min (healthy)  0.0.0.0:3001->3000/tcp
captia-bms-influxdb   Up 23 min (healthy)  0.0.0.0:8087->8086/tcp
captia-bms-loki       Up 23 min (healthy)  0.0.0.0:3100->3100/tcp
captia-bms-mosquitto  Up 23 min (healthy)  0.0.0.0:1884->1883, 9102->9001
captia-bms-prometheus Up 23 min (healthy)  0.0.0.0:9090->9090/tcp
captia-bms-promtail   Up 23 min            (sidecar)
captia-bms-redis      Up 23 min (healthy)  6379/tcp
captia-bms-telegraf   Up 11 min (healthy)  9273/tcp internal
+ uvicorn host (bms-data-generator)        127.0.0.1:8121
```

8 contenedores **(healthy)** + uvicorn host.

## 4. Variables de entorno (resumen agrupado)

| Grupo | Var | Default / Estado |
|---|---|---|
| Compose | `CAPTIA_NETWORK_NAME` | `captia-bms-network` (intencional, aislado) |
| MQTT | `MQTT_PORT_HOST`, `MQTT_WS_PORT_HOST` | 1884, 9102 (evita choque CAPTIA-connect) |
| MQTT | `CAPTIA_ENV`, `CAPTIA_TENANT`, `CAPTIA_SITE` | `dev`, `default`, `ies_simarro` |
| InfluxDB | `INFLUXDB_TOKEN`, `INFLUXDB_ADMIN_PASSWORD` | **obligatorios** (`init_env.sh` los genera) |
| Grafana | `GRAFANA_ADMIN_PASSWORD` | `admin` (dev) — hardening en SECURITY.md |
| BMS | `BMS_API_TOKEN` | **obligatorio** |
| BMS | `BMS_GENERATOR_PORT_HOST` | `8121` (evita choque con CAPTIA-connect events-dashboard) |
| BMS | `BMS_N_AULAS`, `BMS_SEED`, `BMS_FAULTS_ENABLED` | 10, 42, false |

44 variables documentadas en `.env.example`.

## 5. Top archivos por tamaño

| KB | Archivo |
|---|---|
| 769 | `docs/influxdb-simarro-buckets.pptx` |
| 742 | `docs/captia-connect-partner-integration.pptx` |
| 555 | `vendor/synthetic-generator/tests/fixtures/faraone_seed42_1day.csv` |
| 500 | `vendor/synthetic-generator/tests/fixtures/grasso_frio_seed42_1day.csv` |
| 400 | `vendor/synthetic-generator/tests/fixtures/ies_simarro_seed42_1day.csv` |

Sin binarios anómalos.

## 6. Riesgos visibles

- 2 TODOs en `query_service.py` (Redis cache hook explícito post-gap #5).
- 0 paths absolutos (Linux/Windows).
- 0 imágenes Docker `latest`.
- 0 secretos reales (placeholders `CHANGE_ME_USE_OPENSSL_RAND` + auto-gen vía `init_env.sh`).

## 7. Resumen ejecutivo

| Métrica | Valor |
|---|---|
| Tamaño repo (sin .git/.venv) | ~15 MB |
| LOC Python (sin vendor) | ~6 600 |
| LOC vendor | ~2 581 |
| Total LOC | ~9 200 |
| Commits `main` | 48 (+ ramas dependabot) |
| Tests totales | ~62 |
| Specs SDD + physics | 25 docs |
| Servicios Docker | 9 (todos pinned) |
| Workflows CI/CD | 3 |

### 10 hallazgos para auditoría profunda posterior

1. **`bms_signal_alias` es nuevo** y todavía con 1 test — área prioritaria para QA.
2. **2 TODOs activos** en `query_service.py` (Redis cache).
3. **Sin `[tool.coverage]`** ni reporte de coverage en CI.
4. **Endpoints `/v1/*` sin rate limit** — DoS posible.
5. **Physics validation specs** ortogonales a SDD — riesgo de drift.
6. **CI no levanta stack real** — solo compose syntax check, no E2E.
7. **Branches dependabot abiertas** sin PR visibles.
8. **Healthcheck Telegraf** = `pgrep -f telegraf` (menos riguroso que `wget :9273/metrics` upstream).
9. **`init_env.sh` no documentado** prominente en QUICKSTART (bypass risk).
10. **Python 3.12 mínimo** sin ADR justificándolo (compatibilidad con CAPTIA legacy 3.10).
