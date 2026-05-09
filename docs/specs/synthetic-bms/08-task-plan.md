# 08 — Task plan (trazabilidad)

## Context

Plan de tareas con trazabilidad spec→tarea→test. Generado a partir del plan de implementación inicial (mantenido por los maintainers fuera del repo).

## Tabla maestra

| ID | Fase | Tarea | RF/RNF | Archivos clave | Tests | Riesgo |
|----|------|-------|--------|----------------|-------|--------|
| T-001 | 0 | gitignore/dockerignore/editorconfig | RNF-12 | `.gitignore`, `.dockerignore`, `.editorconfig` | n/a | bajo |
| T-002 | 0 | `.env.example` agrupado por servicio | RNF-12, AC-10 | `.env.example` | n/a | bajo |
| T-003 | 0 | `pyproject.toml` raíz workspace | RNF-12 | `pyproject.toml` | smoke `uv sync` | bajo |
| T-004 | 0 | `CLAUDE.md` ≤200 líneas | ADR-012 | `CLAUDE.md` | n/a | bajo |
| T-005 | 0 | `.claude/README.md` y `settings.local.json` | ADR-012 | `.claude/{README,settings.local.json}` | n/a | bajo |
| T-006 | 0 | 6 subagentes especializados | ADR-012 | `.claude/agents/*.md` | n/a | bajo |
| T-007 | 0 | 5 reglas estables `.claude/rules/` | ADR-012 | `.claude/rules/*.md` | n/a | bajo |
| T-008 | 1 | `00-research-report.md` | trazabilidad RF/RNF | `docs/specs/synthetic-bms/00-research-report.md` | n/a | bajo |
| T-009 | 1 | `00-open-questions.md` | trazabilidad | `00-open-questions.md` | n/a | bajo |
| T-010 | 1 | `00-repo-map.md` | trazabilidad | `00-repo-map.md` | n/a | bajo |
| T-011 | 2 | `01-product-spec.md` | RF-01..RF-12 | `01-product-spec.md` | AC-01..AC-10 | bajo |
| T-012 | 2 | `02-domain-spec.md` | RF-03, RF-05 | `02-domain-spec.md` | DC-01..DC-05 | medio |
| T-013 | 2 | `03-architecture-spec.md` | ADR-001..ADR-015 | `03-architecture-spec.md` | AR-01..AR-05 | medio |
| T-014 | 2 | `04-infra-spec.md` | RNF-08, RNF-11 | `04-infra-spec.md` | IN-01..IN-08 | medio |
| T-015 | 2 | `05-observability-spec.md` | RNF-04 | `05-observability-spec.md` | OB-01..OB-06 | medio |
| T-016 | 2 | `06-api-and-ui-spec.md` | RNF-05 | `06-api-and-ui-spec.md` | API-01..API-06 | medio |
| T-017 | 2 | `07-testing-spec.md` | RNF-09 | `07-testing-spec.md` | TS-01..TS-05 | medio |
| T-018 | 2 | `08-task-plan.md` | trazabilidad | `08-task-plan.md` | n/a | bajo |
| T-019 | 2 | `09-decision-log.md` | ADR-001..ADR-015 | `09-decision-log.md` | n/a | bajo |
| T-020 | 2 | `10-validation-checklist.md` | AC-01..AC-10 | `10-validation-checklist.md` | n/a | bajo |
| T-021 | 2 | `STATUS.md` inicial | trazabilidad | `STATUS.md` | n/a | bajo |
| T-022 | 3 | Vendoring `synthetic-generator` | ADR-001 | `vendor/synthetic-generator/`, `VENDOR.md` | uv sync OK | medio |
| T-023 | 3 | Validar tests vendor | ADR-001 | n/a | `pytest vendor` | bajo |
| T-024 | 4 | Bootstrap `bms_calibration` package | RF-09 | `extensions/bms_calibration/{pyproject,src/__init__,tests/conftest}` | uv sync | bajo |
| T-025 | 4 | TDD `school_calendar.py` | RF-07 | `school_calendar.py` + tests | DC-03 | bajo |
| T-026 | 4 | TDD `faults.py` (FaultInjector) | RF-09, ADR-010 | `faults.py` + tests | DC-04 | medio |
| T-027 | 4 | `physics_overrides.py` (hooks) | L-01 | `physics_overrides.py` | n/a | bajo |
| T-028 | 4 | Snapshot determinism test | DC-02 | `tests/test_determinism.py` | snapshot | bajo |
| T-029 | 5 | Bootstrap `bms-data-generator` | RNF-11 | `modules/bms-data-generator/{pyproject,src,tests}` | n/a | bajo |
| T-030 | 5 | TDD `config.py` Pydantic Settings | RNF-12 | `config.py` + test | TS-01 | bajo |
| T-031 | 5 | TDD `metrics.py` | OB-01 | `metrics.py` + test | TS-01 | bajo |
| T-032 | 5 | TDD `api/health.py` | API-01 | `api/health.py` + test | TS-01, API-01 | bajo |
| T-033 | 5 | TDD `services/runner_service.py` | RF-11 | `runner_service.py` + test | TS-01 | medio |
| T-034 | 5 | TDD `api/control.py` con auth | API-02..API-04 | `api/control.py` + test | TS-02 | medio |
| T-035 | 5 | TDD `services/dump_service.py` y `api/datasets.py` | RF-12, API-06 | `dump_service.py`, `api/datasets.py` | TS-02 | medio |
| T-036 | 5 | Logging estructurado JSON | OB-02 | `logging_config.py` | OB-02 | bajo |
| T-037 | 5 | Dockerfile multi-stage | RNF-11 | `modules/bms-data-generator/Dockerfile` | docker build | medio |
| T-038 | 6 | `compose/base.yaml` (mosquitto, influxdb, redis, telegraf, grafana) | IN-01..IN-08 | `compose/base.yaml`, `infra/mosquitto/`, `infra/telegraf/`, `infra/grafana/Dockerfile` | IN-01 | alto |
| T-039 | 6 | `compose/data-plane-init.yaml` + buckets + tareas Flux | IN-06, IN-07 | `compose/data-plane-init.yaml`, `infra/influxdb/init/`, `infra/influxdb/tasks/` | IN-06, IN-07 | alto |
| T-040 | 6 | `compose/observability.yaml` + configs prometheus/loki/promtail | OB-03, OB-06 | `compose/observability.yaml`, `infra/prometheus/`, `infra/loki/`, `infra/promtail/` | OB-03 | medio |
| T-041 | 6 | `compose/generator.yaml` | IN-01 | `compose/generator.yaml` | IN-01 | medio |
| T-042 | 7 | 4 configs scenario YAML + domain/variables/faults | RF-04, RF-09 | `config/projects/*.yaml`, `config/domains/bms_classrooms/*.yaml` | DC-04 | medio |
| T-043 | 8 | Provisioning datasources Grafana | OB-04 | `infra/grafana/provisioning/` | OB-04 | bajo |
| T-044 | 8 | 4 dashboards JSON | OB-05 | `infra/grafana/dashboards/*.json` | OB-05 | medio |
| T-045 | 9 | `Taskfile.yml` | comandos task | `Taskfile.yml` | n/a | bajo |
| T-046 | 9 | Scripts smoke (preflight, mqtt, influx, grafana, schema, dump) | AC-02, AC-08 | `scripts/*.sh` | AC-02 | medio |
| T-047 | 9 | `Makefile` wrapper | comandos make | `Makefile` | n/a | bajo |
| T-048 | 10 | E2E Caso A pipeline IoT | UC-A | `tests/e2e/test_pipeline_iot.py` | AC-03 | alto |
| T-049 | 10 | E2E Casos B/C/D | UC-B, UC-C, UC-D | `tests/e2e/test_{dump_caseB,faults_caseC,iaq_caseD}.py` | AC-04, AC-05 | alto |
| T-050 | 10 | Ejecutar checklist `10-validation-checklist.md` completa | AC-01..AC-10 | `STATUS.md` | AC-01..AC-10 | medio |
| T-051 | 10 | Revisión cruzada por subagentes | calidad final | n/a | veredicto PASS | medio |

## Total: 51 tareas en 10 fases.

## Convenciones

- Cada tarea **commit**: `feat(<scope>): <descripcion>` para feature, `chore`, `docs`, `test` según corresponda.
- Cada tarea **test asociado** debe pasar antes de cerrar.
- `STATUS.md` se actualiza tras cada tarea.

## Próxima tarea

Ver `STATUS.md` campo "Próximo paso".
