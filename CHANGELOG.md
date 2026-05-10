# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

_Sin cambios todavía. Próximos cambios listados aquí antes del siguiente release._

## [0.2.1] - 2026-05-10

Patch release con fixes de pipeline CI/CD aplicados tras v0.2.0. **Cero
cambios funcionales del código del generator** — la imagen Docker `0.2.1`
es funcionalmente idéntica a `0.2.0` (solo `ruff format` + sin cambios
en runtime).

### Fixed

- **Lint (`ruff check`)** — `UP028: Replace 'yield' over 'for' loop with 'yield from'`
  en `extensions/bms_signal_alias/src/bms_signal_alias/derivations.py:251`.
- **Security workflow — gitleaks** — `gitleaks-action@v2` requiere licencia
  comercial para repos pertenecientes a organizaciones (ver
  https://gitleaks.io/products.html). Sustituido por descarga del binario
  OSS `gitleaks v8.21.2` ejecutado directamente. Mismo motor, mismas
  reglas, sin licencia.
- **Security workflow — trivy** — `aquasecurity/trivy-action@<version>`
  no resuelve porque las tags reales del repo upstream son `vX.Y.Z` (con
  prefijo `v`) y la sintaxis `@X.Y.Z` falla. Cambiado a `@master`
  (recomendado por aquasecurity en su README).

### Style

- **`ruff format`** aplicado a 3 archivos: `derivations.py`,
  `runner_service.py`, `bootstrap.py`. Solo line breaks y alineación de
  paréntesis; cero cambios funcionales.

### Workflows GREEN tras esta release

```
CI (5 jobs)         ✓ Validate compose  ✓ Lint  ✓ Tests (Python 3.12)
                    ✓ E2E smoke         ✓ Build Docker image
Security (3 jobs)   ✓ gitleaks OSS  ✓ pip-audit  ✓ trivy (master)
Deploy Docs         ✓ MkDocs → GitHub Pages
Release v0.2.1      ✓ GHCR image + GitHub release
```

### Image

```
ghcr.io/captia-technology/captia-synthetic-data-bms/bms-data-generator:0.2.1
ghcr.io/captia-technology/captia-synthetic-data-bms/bms-data-generator:latest
                                                    sha256:b7a6da8b... (377 MB)
```

## [0.2.0] - 2026-05-10

**Fase 12 — Pipeline E2E + signal mapping completo.**

Primera release que cierra el gap "drop-in replacement de simarro-prod":
las **30 variables canónicas** del PPTX simarro-prod slide 14 están
todas generadas por el stack standalone, con catálogo metadata poblado
**automáticamente desde el primer deploy**. El pipeline MQTT → Telegraf
→ InfluxDB → Grafana queda sólido tras debug E2E exhaustivo (corregida
la causa raíz del silent data drop).

### Added

- **`tools/metadata-bootstrap/`** — nuevo servicio Python (500 LOC,
  adaptado de `captia-connect/tools/metadata-bootstrap`). Pobla
  `captia_metadata` AUTOMÁTICAMENTE en cada deploy (encadenado tras
  `influx-init`). Escribe `N_aulas × 33` rows a `captia_point_meta` +
  1 a `captia_domain_meta`. Soporta `production_name` override y lee
  también `derivations.yaml`. ADR-020.
- **`config/domains/bms_classrooms/derivations.yaml`** — 12 vars derivadas
  vendor → producción (cierra L-PV-01). Cubre las 30 vars del PPTX
  simarro-prod slide 14: `temperature-indoor`, `t-voc`, `max-sound-level`,
  `aire`, `aire_state`, `fan_speed_01..03`, `fan_speed_03_state`,
  `light_01..02`, `valve_state`. ADR-021.
- **`extensions/bms_signal_alias/derivations.py`** — engine declarativo
  con 6 transforms (`passthrough`, `jitter`, `linear`, `bool_to_speed`,
  `bool_to_intensity`, `threshold_to_bool`). Determinismo bit-a-bit via
  `np.random.default_rng(seed=hash(name|asset|ts_5s_bucket))`.
- **`AliasSinkAdapter` extendido** para emitir originales + derivados.
  Counter `derived_count` expuesto.
- **MQTTX-Web service** en `compose/observability.yaml` — UI MQTT con
  config preconfigurada en `infra/mqttx/captia-bms-mqttx-config.json`
  (auto-import de connection + 7 subscriptions + 2 scripts decode).
- **`make verify-metadata`** — valida ≥ N×33 entries en
  `captia_point_meta` + 1 en `captia_domain_meta`.
- **`make metadata-bootstrap`** — re-ejecuta el bootstrap manualmente.
- **`docs/operations/troubleshooting.md`** — entradas nuevas para "Telegraf
  reporta Wrote pero datos no aparecen" y "Múltiples instancias compartiendo
  client_id".

### Fixed

- **Pipeline E2E silent data drop** (ADR-022): Telegraf
  `persistent_session = true` causaba que tras restart entregase el queue
  persistente del broker con timestamps históricos corruptos, que InfluxDB
  rechazaba silenciosamente por retention policy. Cambiado a `false`.
  `agent.statefile` eliminado (estaba ligado al persistent session).
- **MQTT client_id collisions**: el config YAML del scenario tenía
  `client_id: "captia-bms-generator-demo"` fijo. Si dos procesos
  publicaban con el mismo ID (ej. host zombi + container), MQTT spec
  fuerza al broker a desconectar el anterior y entran en loop infinito.
  `runner_service.py::_build_runner` ahora appende UUID hex(8) al
  client_id configurado.
- **`RunnerService.stop()` no paraba el runner del vendor**: el `stop()`
  previo solo marcaba el job como "stopped" pero
  `ScenarioRunner.run_live()` (vendor) seguía publicando indefinidamente.
  Ahora `_Job.runner` mantiene referencia al runner y `stop()` setea
  `runner._running = False`.
- **Métricas Prometheus no se actualizaban**: nuevo
  `_MetricsCountingSink` wrapper que instrumenta
  `captia_bms_messages_published_total{topic}`, `captia_bms_connected`,
  `captia_bms_active_jobs` sin tocar vendor.
- **Mosquitto `max_inflight_messages 200 → 1000`** — red de seguridad
  ante bursts de reconexiones.
- **`valve_control` ahora va a `state_events`** — añadido al
  `processors.clone.tagpass` de Telegraf (no matcheaba ningún glob).
- **Variables `*_audit` residuales borradas** del bucket `telemetry`.

### Documentation

- **Drift audit profundo**: corregidos los 4 grupos de drifts identificados:
  - "6 buckets" → "7 buckets" (`telemetry_events` añadido) en 6 archivos.
  - "21 vars" → "33 vars (21 vendor + 12 derived)" en 5+ archivos.
  - `persistent_session = false` documentado en troubleshooting + ADR-022.
  - `metadata-bootstrap` documentado en specs (04, 05, 09, STATUS) +
    `data-flow.md` con paso "Pre-requisito — bootstrap del catálogo".
  - Derivations documentadas en `02-domain-spec.md` y `data-flow.md`.
- **L-PV-01 cerrado** en `docs/specs/digital-twin-bms-physics-validation/00-open-questions.md`.
- **`docs/operations/visualizing-data.md`** actualizado con `make verify-metadata`.
- **3 nuevos ADRs**: 020 (metadata-bootstrap), 021 (derivations), 022
  (persistent_session=false).

### Security

- **Sanitización pre-público**: eliminadas referencias a tenant interno
  (`influx.simarro-prod.captiatechnology.com`), rutas absolutas Windows
  (`C:\CAPTIA\...`) en docs y scripts. Aviso de revisión añadido para
  PPTX internos en `docs/archive/presentaciones/README.md`.
- **README "Quiénes somos"** reescrito con copy literal de captia.ai
  (claim, 5 productos, sectores objetivo).

### Verification

- 331 puntos escritos a `captia_metadata` (1 + 330 = 33 vars × 10 aulas).
- Job live con 5 aulas → 12/12 derivations llegan al bucket telemetry.
- 30/30 vars del PPTX simarro-prod slide 14 cubiertas.
- `make verify-metadata` OK; `make smoke` OK.

### Image

```
ghcr.io/captia-technology/captia-synthetic-data-bms/bms-data-generator:0.2.0
                                                    sha256:4a29eee3... (377 MB)
```

## [Pre-2026-05-10]

### Added
- **45 didactic notebooks** under `notebooks/` covering the 11 use cases
  (A-J + extra) of the IES Simarro AI & Big Data course. Each notebook
  follows an 18-section template, uses `seed=42` and ships deterministic
  mocks under `notebooks/_data/`. Helpers in `notebooks/_common/`
  (schema constants, InfluxDB client with `.env`, mock generators,
  plotting, template outline).
- **Notebook builder** under `scripts/build_notebooks/` (one module per
  case) and `scripts/build_notebook_data.py` for idempotent regeneration.
- **Web documentation** restructured: 28 new markdowns across
  `docs/use-cases/`, `docs/contracts/`, `docs/validation/`,
  `docs/operations/`, `docs/notebooks/`, `docs/getting-started/` and
  `docs/architecture/`. Updated `mkdocs.yml` navigation, builds with
  zero warnings.
- **Audit phase 11**: `docs/audit/USE_CASE_MATRIX.md`,
  `docs/audit/NOTEBOOK_PLAN.md`, `docs/audit/DOCS_REPORT.md`. STATUS
  updated.
- **Notebook integrity test suite** in
  `tests/integration/test_notebooks_integrity.py` (183 parametrised
  checks): nbformat 4 validity, traceable headers (case + medallion +
  spec), CAPTIA schema citation, no inline secrets, importability of
  `notebooks._common` without matplotlib, deterministic mocks.
- **Taskfile commands**: `task notebooks:data`, `task notebooks:build`,
  `task notebooks:test`, `task notebooks:lab`, `task docs:build`,
  `task docs:serve`.
- Public-release polish: Apache-2.0 license, NOTICE, CODE_OF_CONDUCT,
  CONTRIBUTING, SECURITY, CHANGELOG, GitHub workflows, dependabot,
  issue/PR templates.

### Changed
- Vendor build slimmed to `bms_classrooms` only (`PATCHES/001-bms-only.patch`).
- All absolute paths removed from configs and docs in favour of relative
  references to the upstream repository.
- Contact email updated to `jaime.sendra@captiatechnology.com`.
- README root extended with _Notebooks didácticos_ section and updated
  documentation map (web sections + specs + archive).

## [0.1.0] - 2026-05-09

### Added
- Initial release of `CAPTIA-SYNTHETIC-DATA-BMS`.
- Spec-driven package under `docs/specs/synthetic-bms/` (00-research,
  01-product, 02-domain, 03-architecture, 04-infra, 05-observability,
  06-api-and-ui, 07-testing, 08-task-plan, 09-decision-log,
  10-validation-checklist, STATUS).
- Vendored snapshot of `synthetic-generator` engine (hexagonal core,
  ports, sinks) under `vendor/synthetic-generator/`.
- `extensions/bms_calibration/` with `ValenciaSchoolCalendar`, four-type
  HVAC `FaultInjector` and physics override hooks.
- `modules/bms-data-generator/` FastAPI control plane: `/healthz`,
  `/readyz`, `/metrics`, `/v1/control/{start,stop,status}`,
  `/v1/datasets/export`, `/v1/datasets/jobs/{id}`. Bearer-token auth.
  Multi-stage `Dockerfile`.
- Docker stack via Compose v2: Mosquitto 2.0.18, Telegraf 1.32,
  InfluxDB 2.7, Redis 7-alpine, Grafana 11.4 (build local), Prometheus
  v2.49.1, Loki / Promtail 2.9.4.
- One-shot `influx-init` job that creates 6 buckets and 5 Flux downsample
  tasks following the canonical CAPTIA schema.
- Grafana dashboards (provisioned): overview, IAQ (case D), consumption
  (case B), faults (case C).
- Four scenario YAMLs (`bms_v1_demo`, `caseB_consumption`,
  `caseC_faults`, `caseD_iaq`) plus domain catalog and faults config.
- Taskfile, Makefile and shell scripts for `preflight`, `wait_healthy`,
  `smoke_{mqtt,influx,grafana}`, `verify_canonical_schema`,
  `export_dump`, `update_vendor`.
- 44 root tests (32 unit + 11 integration + 1 snapshot) passing on the
  workspace; 129 vendor unit tests passing.
- `.claude/` governance: 6 specialised subagents, 5 stable rules,
  language and vendoring policies.

### Security
- Mosquitto runs in anonymous mode by default — explicitly marked as
  development-only in `infra/mosquitto/mosquitto.conf` and `SECURITY.md`.
- API token (`BMS_API_TOKEN`) optional locally, mandatory in compose
  through `${BMS_API_TOKEN:?required}`.

[Unreleased]: https://github.com/captia-technology/captia-synthetic-data-bms/compare/v0.2.1...HEAD
[0.2.1]: https://github.com/captia-technology/captia-synthetic-data-bms/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/captia-technology/captia-synthetic-data-bms/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/captia-technology/captia-synthetic-data-bms/releases/tag/v0.1.0
