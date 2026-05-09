# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Public-release polish: Apache-2.0 license, NOTICE, CODE_OF_CONDUCT,
  CONTRIBUTING, SECURITY, CHANGELOG, GitHub workflows, dependabot,
  issue/PR templates.

### Changed
- Vendor build slimmed to `bms_classrooms` only (`PATCHES/001-bms-only.patch`).
- All absolute paths removed from configs and docs in favour of relative
  references to the upstream repository.
- Contact email updated to `jaime.sendra@captiatechnology.com`.

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

[Unreleased]: https://github.com/jaimesendra/captia-synthetic-data-bms/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/jaimesendra/captia-synthetic-data-bms/releases/tag/v0.1.0
