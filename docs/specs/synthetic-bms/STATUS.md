# STATUS — synthetic-bms

**Última actualización**: 2026-05-10
**Fase actual**: 12 (Pipeline E2E + metadata-bootstrap + signal mapping completo) — COMPLETADA
**Tarea en curso**: ninguna
**Última tarea completada**: ACCIÓN 1 — 12 derivations production_name (cierra L-PV-01)
**Tests verdes**: 46 PASS (workspace) + 129 PASS (vendor unit), 0 failed
**Bloqueos**: ninguno
**Próxima tarea**: tag `v0.2.0` con changelog completo Fase 12

## Cambios en Fase 12 (2026-05-10)

- **Pipeline E2E debug + fix definitivo** (commit `9eba9c8`): Telegraf
  `persistent_session = true` causaba silent data drop tras backlog
  acumulado en queue del broker → `false` por default ahora.
- **Cliente MQTT único por instancia** (`9669e94`): UUID hex(8) appended
  al `client_id` configurado para evitar colisiones MQTT spec.
- **`RunnerService.stop()` señaliza vendor runner**: setea
  `runner._running = False` para graceful shutdown sin threads zombi.
- **`_MetricsCountingSink` wrapper**: instrumenta Prometheus counters
  (`captia_bms_messages_published_total`, `connected`, `active_jobs`)
  sin tocar vendor.
- **`max_inflight_messages 200 → 1000`** en Mosquitto.
- **MQTTX-Web service** (`compose/observability.yaml`): UI MQTT preconfigurada
  con import JSON listo (`infra/mqttx/captia-bms-mqttx-config.json`).
- **`tools/metadata-bootstrap/`** (`c87ca6f`): nuevo servicio Python (500 LOC,
  adaptado de captia-connect) que pobla `captia_metadata` AUTOMÁTICAMENTE
  en cada deploy. 21 vendor + 12 derived = 33 vars × N aulas.
- **12 derivations vendor → production** (`88ff7d7`): cierra L-PV-01
  completo. Nuevo `derivations.yaml` + `derivations.py` con 6 transforms.
  Cubre las 30 vars del PPTX simarro-prod slide 14.
- **Auditoría docs cross-repo**: drifts corregidos (6→7 buckets, 21→33
  vars, persistent_session documented, metadata-bootstrap doc, derivations
  doc).

## Histórico

| Fecha | Hito |
|-------|------|
| 2026-05-09 | Inicio Fase 0. Bootstrap repo + `.claude` config (T-001..T-007) |
| 2026-05-09 | Fin Fase 1 (research docs 00-*) e inicio Fase 2 |
| 2026-05-09 | Fin Fase 2 (specs SDD 01-10) e inicio Fase 3 |
| 2026-05-09 | Fin Fase 3 (vendoring synthetic-generator) e inicio Fase 4 |
| 2026-05-09 | Fin Fase 4 (extensions bms_calibration) e inicio Fase 5 |
| 2026-05-09 | Fin Fase 5 (microservicio FastAPI) e inicio Fase 6 |
| 2026-05-09 | Fin Fase 6 (Docker infra) e inicio Fase 7 |
| 2026-05-09 | Fin Fase 7 (4 configs scenario) e inicio Fase 8 |
| 2026-05-09 | Fin Fase 8 (4 dashboards Grafana) e inicio Fase 9 |
| 2026-05-09 | Fin Fase 9 (Taskfile + scripts) e inicio Fase 10 |
| 2026-05-09 | Fin Fase 10 — v1 lista (44 tests verdes, ruff limpio) |
| 2026-05-09 | Fin Fase 11 — repo public-ready (vendor BMS-only, paths sanitizados, comunidad GitHub, CI/CD, wiring real, quickstart, Mermaid, README pro) |

## Métricas v1 (post-polish)

- **Commits**: 25 (uno por paso semántico).
- **Archivos rastreados**: ≈ 145 tras vendor slim (eliminados industrial / manufacturing).
- **Líneas escritas (excl. vendor)**: ≈ 6 200.
- **Tests verdes**: 46 (workspace) + 129 (vendor).
- **Lint**: `ruff check .` y `ruff format --check .` PASS.
- **Workspace `uv sync`**: 43 packages.
- **Imágenes Docker**: 9, todas con tag fijo (no `latest`).
- **Specs SDD**: 14 documentos en `docs/specs/synthetic-bms/` con diagramas Mermaid.

## Decisiones nuevas (Fase 11)

- **ADR-016 implícito** — Vendor slimmed to BMS-only (`vendor/synthetic-generator/PATCHES/001-bms-only.patch`). Removed `industrial_refrigeration` y `discrete_manufacturing`.
- **Licencia** — Apache License 2.0 (en lugar de "Proprietary" inicial). `LICENSE` + `NOTICE` añadidos.
- **Email contacto** — `jaime.sendra@captiatechnology.com` en pyproject, README, SECURITY, CODE_OF_CONDUCT.
- **Sanitización paths** — Eliminadas todas las referencias absolutas `C:\CAPTIA\...` en docs, scripts y configs.
- **Despliegue one-shot** — `task quickstart` y `scripts/init_env.sh` autogenera `.env` con secretos aleatorios.
- **Wiring real** — `RunnerService` y `DumpService` ahora invocan a `vendor.synthetic_generator.core.runner.ScenarioRunner` en threads daemon, con factory inyectable para tests rápidos.
- **CI/CD** — `.github/workflows/{ci,security,release}.yml` + `pre-commit` + `dependabot.yml`.

## Pendientes post-publicación

1. **Calibración real (L-01)** — sigue como hooks. Requiere parámetros calibrados con datos reales del IES Simarro.
2. **Performance benchmarks** — `tests/performance/` como TODO; AC-03 (≥ 700 pts/aula·h) sin medir formalmente.
3. **Smoke E2E con stack levantado** — los workflows CI no levantan docker. Validación completa requiere local o un job CI con `services:` adicional.
4. **Hardening producción** — checklist en `SECURITY.md`. No abordado v0.1.0.
5. **Dashboards extra** — actuales son base; añadir uno por aula y uno por job en futuras versiones.

## Próximos pasos recomendados

1. `git tag v0.1.0` + `git push --tags` (esto dispara `release.yml` y publica imagen en GHCR).
2. Crear repo público en GitHub: `gh repo create jaimesendra/captia-synthetic-data-bms --public`.
3. Push: `git remote add origin git@github.com:jaimesendra/captia-synthetic-data-bms.git && git push -u origin master:main`.
4. Configurar branch protection en `main` (requerir CI verde + 1 review).
5. Habilitar `dependabot` y `Dependency graph` en Settings → Security.
6. Ajustar `CODEOWNERS` si se incorporan más maintainers.
