# 00 — Mapa de repositorios

## 1. Mapa target — `captia-synthetic-data-bms/` (raíz del repo)

```
.
├── .claude/                          # Config Claude Code (READ-ONLY salvo ADR)
│   ├── README.md
│   ├── settings.local.json
│   ├── agents/                       # 6 subagentes especializados
│   │   ├── repo-cartographer.md
│   │   ├── spec-architect.md
│   │   ├── infra-reviewer.md
│   │   ├── observability-reviewer.md
│   │   ├── qa-reviewer.md
│   │   └── security-reviewer.md
│   └── rules/                        # 5 reglas estables
│       ├── 001-spec-driven-development.md
│       ├── 002-captia-canonical-schema.md
│       ├── 003-vendoring-policy.md
│       ├── 004-docker-compose-conventions.md
│       └── 005-language-policy.md
├── .env.example
├── .gitignore
├── .dockerignore
├── .editorconfig
├── CLAUDE.md                         # ≤200 líneas
├── README.md
├── pyproject.toml                    # Workspace uv
├── uv.lock
├── Taskfile.yml
├── Makefile
├── docker-compose.yml                # opcional, alias de COMPOSE_FILE
├── compose/
│   ├── base.yaml                     # mosquitto + influxdb + redis + telegraf + grafana
│   ├── observability.yaml            # prometheus + loki + promtail
│   ├── generator.yaml                # bms-data-generator
│   └── data-plane-init.yaml          # influx-init (one-shot)
├── docs/
│   ├── CAPTIA_Informe_CasosDeUso_DatosSinteticos.md
│   ├── CENTINELA_Guia_Alumnos_v4.md
│   ├── MEDALLION_Arquitectura_Guia_Referencia.md
│   ├── captia-connect-partner-integration.pptx
│   ├── influxdb-simarro-buckets.pptx
│   └── specs/
│       └── synthetic-bms/
│           ├── 00-research-report.md
│           ├── 00-open-questions.md
│           ├── 00-repo-map.md
│           ├── 01-product-spec.md
│           ├── 02-domain-spec.md
│           ├── 03-architecture-spec.md
│           ├── 04-infra-spec.md
│           ├── 05-observability-spec.md
│           ├── 06-api-and-ui-spec.md
│           ├── 07-testing-spec.md
│           ├── 08-task-plan.md
│           ├── 09-decision-log.md
│           ├── 10-validation-checklist.md
│           └── STATUS.md
├── modules/
│   └── bms-data-generator/           # Microservicio FastAPI
│       ├── pyproject.toml
│       ├── Dockerfile
│       ├── README.md
│       ├── src/bms_data_generator/
│       │   ├── __init__.py
│       │   ├── __main__.py
│       │   ├── main.py
│       │   ├── config.py
│       │   ├── metrics.py
│       │   ├── logging_config.py
│       │   ├── api/
│       │   │   ├── __init__.py
│       │   │   ├── control.py
│       │   │   ├── datasets.py
│       │   │   └── health.py
│       │   └── services/
│       │       ├── __init__.py
│       │       ├── runner_service.py
│       │       ├── dump_service.py
│       │       └── calibration_loader.py
│       └── tests/
│           ├── conftest.py
│           ├── unit/
│           └── integration/
├── extensions/
│   └── bms_calibration/              # Calibración local + fault injection
│       ├── pyproject.toml
│       ├── src/bms_calibration/
│       │   ├── __init__.py
│       │   ├── faults.py
│       │   ├── school_calendar.py
│       │   └── physics_overrides.py
│       └── tests/
├── vendor/
│   └── synthetic-generator/          # Vendoring read-only
│       ├── VENDOR.md
│       └── ...
├── config/
│   ├── projects/
│   │   ├── bms_v1_demo.yaml
│   │   ├── bms_v1_caseB_consumption.yaml
│   │   ├── bms_v1_caseC_faults.yaml
│   │   └── bms_v1_caseD_iaq.yaml
│   └── domains/
│       └── bms_classrooms/
│           ├── domain.yaml
│           ├── variables.yaml
│           └── faults.yaml
├── infra/
│   ├── mosquitto/mosquitto.conf
│   ├── telegraf/telegraf.conf
│   ├── influxdb/
│   │   ├── init/init_buckets_tasks.sh
│   │   └── tasks/*.flux
│   ├── grafana/
│   │   ├── Dockerfile
│   │   ├── provisioning/{datasources,dashboards}/
│   │   └── dashboards/*.json
│   ├── prometheus/{prometheus.yml,rules/}
│   ├── loki/loki-config.yml
│   └── promtail/promtail-config.yml
├── scripts/
│   ├── preflight.sh
│   ├── smoke_mqtt.sh
│   ├── smoke_influx.sh
│   ├── smoke_grafana.sh
│   ├── verify_canonical_schema.sh
│   ├── export_dump.sh
│   └── update_vendor.sh
└── tests/e2e/
    ├── conftest.py
    ├── test_pipeline_iot.py
    ├── test_dump_caseB.py
    ├── test_faults_caseC.py
    └── test_iaq_caseD.py
```

## 2. Mapa repo de referencia — `captia-connect/` (upstream interno, vendorizado)

```
captia-connect/
├── .claude/                          # 40+ skills, governance, settings.local.json
├── compose/                          # 20+ archivos compose (base, observability, edge, events, etc.)
├── modules/
│   ├── ingest/                       # mosquitto.conf + telegraf.conf (no Python)
│   ├── data-plane/                   # init_influx_buckets_tasks.sh + tasks/*.flux
│   ├── dashboard-adapter/            # FastAPI :8100, Prometheus metrics
│   ├── events-engine/                # Event Rules Engine :8110
│   ├── mqtt-normalizer/              # MQTT → MQTT bridge
│   ├── contracts/                    # MQTT topic naming SSOT
│   └── observability/                # Grafana, Prometheus, Loki configs
├── tools/
│   └── synthetic-generator/          # ⭐ Módulo a vendorizar
│       ├── pyproject.toml
│       ├── Dockerfile
│       ├── src/synthetic_generator/
│       │   ├── core/                 # core engine
│       │   ├── ports/                # interfaces hexagonales
│       │   ├── domains/
│       │   │   ├── bms_classrooms/   # ⭐ Dominio reutilizable
│       │   │   ├── industrial_refrigeration/
│       │   │   └── discrete_manufacturing/
│       │   └── sinks/                # mqtt, file, stdout, null, composite
│       └── tests/                    # unit, integration, snapshot
├── packages/
├── pyproject.toml                    # Workspace uv
├── Makefile                          # wrapper de Taskfile
└── Taskfile.yml                      # Targets: install, lint, test, up, down, smoke
```

## 3. Archivos clave a copiar / replicar

| Origen CAPTIA-CONNECT | Destino BMS | Modificación |
|----------------------|-------------|--------------|
| `tools/synthetic-generator/**` | `vendor/synthetic-generator/` | Copia recursiva read-only |
| `modules/ingest/mosquitto/mosquitto.conf` | `infra/mosquitto/mosquitto.conf` | Mantener literal (paths internos `/mosquitto/data`, `/mosquitto/log`) |
| `modules/ingest/telegraf/telegraf.conf` | `infra/telegraf/telegraf.conf` | Mantener literal (regex tags y schema canónico) |
| `modules/data-plane/scripts/init_influx_buckets_tasks.sh` | `infra/influxdb/init/init_buckets_tasks.sh` | Adaptar paths buckets/tareas |
| `modules/data-plane/tasks/*.flux` | `infra/influxdb/tasks/*.flux` | Copia literal (5 archivos) |
| `modules/observability/grafana/provisioning/` | `infra/grafana/provisioning/` | Adaptar URLs de datasources |
| `modules/observability/loki/loki-config.yml` | `infra/loki/loki-config.yml` | Copia literal |
| `modules/observability/promtail/promtail-config.yml` | `infra/promtail/promtail-config.yml` | Filtrar `compose_project=captia-bms` |
| `modules/observability/prometheus/prometheus.yml` | `infra/prometheus/prometheus.yml` | Reemplazar scrape_configs por servicios BMS |
| `modules/dashboard-adapter/Dockerfile` | `modules/bms-data-generator/Dockerfile` | Plantilla multi-stage |
| `compose/base.yaml` (servicios persistentes) | `compose/base.yaml` | Adaptar contenedores `captia-bms-*`, eliminar dashboard-adapter de base |

## 4. Convenciones extraídas del repo padre

- **Python**: `>=3.12`.
- **Package manager**: `uv` (workspace).
- **Linter/formatter**: `ruff` (target py312, line-length 100).
- **Test framework**: `pytest` con `asyncio_mode = "auto"`, markers en `pyproject.toml`.
- **Layout módulos**: `src/<package_name>/`.
- **Naming**: paquetes snake_case, directorios kebab-case.
- **Container naming**: `captia-<servicio>` (CAPTIA-CONNECT) → `captia-bms-<servicio>` (BMS).
- **Network**: `captia-network` (compartida).
