# Auditoría extrema — STATUS

**Fecha de inicio**: 2026-05-09
**Repo principal**: `captia-synthetic-data-bms` (este repositorio).
**Repo de referencia (contratos)**: `captia-connect` (interno).
**Repo de referencia (estilo docs)**: `captia.ai` (interno).

## Objetivo

Auditar de forma extrema todo el repo `CAPTIA-SYNTHETIC-DATA-BMS`, validar
consistencia completa, ejecutar pruebas E2E reales y dejar `docs/` como
documentación web profesional lista para GitHub Pages.

## Plan en 10 fases

| Fase | Entregable | Estado |
|---|---|---|
| 1 | `docs/audit/STATUS.md` + mapa inicial del repo (`00-repo-map.md`) | ✅ |
| 2 | `CONSISTENCY_MATRIX.md` BMS ↔ CAPTIA-connect (11 áreas, top 5 críticas + top 5 aceptables) | ✅ |
| 3 | `DOCS_RESTRUCTURE_PLAN.md` con `mkdocs.yml` y workflow GitHub Pages | ✅ |
| 4 | `AUDIT_REPORT.md` síntesis + top 20 hallazgos consolidados | ✅ |
| 5 | `E2E_VALIDATION_REPORT.md` con 10 escenarios reales ejecutados | ✅ |
| 6 | `PHYSICAL_REALISM_REPORT.md` modelos físicos vs spec | ✅ |
| 7 | Correcciones mínimas trazables (cada commit referencia el hallazgo) | ✅ |
| 8 | Reestructuración real `docs/` estilo web (migrar archivos según el plan) | ✅ |
| 9 | Setup GitHub Pages (workflow, navegación, índice, enlaces) | ✅ |
| 10 | `ACTION_PLAN.md` + resumen final con evidencias | ✅ |

## Estado del stack al inicio de la auditoría

```
docker compose ps                : 8 servicios (healthy)
uvicorn host (bms-data-generator): vivo (uptime 4 min)
job /v1/control                  : phase=running, mode=live, 10 aulas
Telegraf MQTT consumer           : 40 msg/s, 8800+ mensajes recibidos
InfluxDB telemetry bucket        : 7607+ puntos
state_events bucket              : 1362+ puntos (con tag stat=last)
captia_metadata captia_point_meta: 21 variables
Grafana                          : 4 datasources + 4 dashboards
```

## Reglas no negociables

- Repo principal: `CAPTIA-SYNTHETIC-DATA-BMS`. CAPTIA-connect es **referencia**.
- captia.ai/docs es **referencia de estilo**, no fuente funcional.
- Ningún cambio de contrato sin justificación documentada en `decisions/`.
- Ningún secreto hardcodeado.
- Ninguna imagen Docker `latest`.
- Mantener compatibilidad MQTT / Telegraf / Influx con CAPTIA-connect upstream.
- Toda corrección minima, trazable, validada.
- Cada doc enlaza a rutas reales del repo.
- No declarar éxito sin evidencia (logs, queries, outputs).

## Histórico

- **2026-05-09 18:46** — fase 1 iniciada (`STATUS.md` + mapa).
- **2026-05-09 20:54** — fase 1 cerrada (`00-repo-map.md`).
- **2026-05-09 20:55** — fase 2 cerrada (`CONSISTENCY_MATRIX.md`).
- **2026-05-09 20:56** — fase 3 cerrada (`DOCS_RESTRUCTURE_PLAN.md`).
- **2026-05-09 23:47** — fase 4 cerrada (`AUDIT_REPORT.md` 20 hallazgos: 3 alta, 9 media, 8 baja).
- **2026-05-09 23:52** — fase 5 cerrada (`E2E_VALIDATION_REPORT.md` 10 escenarios E2E + 8 físicos PASS; 2 hallazgos extra H-21 / H-22).
- **2026-05-10 00:05** — fase 6 cerrada (`PHYSICAL_REALISM_REPORT.md` score estimado 0.94, top 10 gaps físicos, evidencia live AULA01); descubrimiento H-23 jitter setpoint excesivo (75 ev/h en `state_events`).
- **2026-05-10 00:10** — fase 7 iniciada — correcciones mínimas priorizadas H-23 (jitter setpoint), L-PV-09 (cooling deshum), L-PV-07 (anti short-cycle).
- **2026-05-10 00:30** — fase 7 cerrada — 3 patches aplicados al vendor (002, 003, 004) con tests de regresión (15 tests nuevos pasando), retrocompatibilidad preservada, suite total 194/194 PASS. Nuevas claves físicas en `domain.yaml` (`setpoint_jitter_std=0.05`, `cooling_dehum_delta=8.0`, `hvac_min_on_minutes=5.0`, `hvac_min_off_minutes=5.0`).
- **2026-05-10 00:35** — fase 8 iniciada — bootstrap MkDocs Material + reorganización `docs/`.
- **2026-05-10 00:55** — fase 8 cerrada — `mkdocs.yml` raíz + Material theme con paleta CAPTIA, `docs/index.md` con flowchart Mermaid + matriz "quiero X", stubs para `getting-started/`, `architecture/`, `physical-model/`, `decisions/`, `audit/`, `archive/`, `specs/`. Legacy CENTINELA / MEDALLION / casos de uso movidos a `docs/archive/`. PPTX a `docs/archive/presentaciones/`. `mkdocs build --clean` PASS sin errores.
- **2026-05-10 00:56** — fase 9 cerrada — `.github/workflows/deploy-docs.yml` con build + deploy a GitHub Pages (path-based trigger sobre `docs/**`, `mkdocs.yml`, workflow propio).
- **2026-05-10 00:57** — fase 10 iniciada — `ACTION_PLAN.md` con priorización final.
- **2026-05-10 01:00** — fase 10 cerrada — `ACTION_PLAN.md` consolida 27 hallazgos abiertos (3 alta · 11 media · 13 baja) con priorización MoSCoW, esfuerzo estimado y roadmap Gantt 4 semanas. Auditoría extrema completa.
- **2026-05-10 01:15** — follow-up Must — H-21 cerrada (PATCH 005 TZ-aware `datetime.now`), H-22 cerrada (PATCH 006 doble scrape Prometheus mode=container/host, verificado live), gap #27 cerrado (`make stream` + `scripts/stream_live.sh`). Suite 194 → **198/198 PASS**. L-PV-02 confirmada cableada vía tests Caso C (live E2E pendiente).
- **2026-05-10 01:20** — Hallazgos abiertos del ACTION_PLAN: **22** (1 alta · 11 media · 10 baja). Único alta restante: **H-01** event payload `ts_ns` vs ISO `ts` — requiere decisión arquitectónica con upstream CAPTIA-connect.
- **2026-05-10 16:30** — bloque Should del ACTION_PLAN — 5 hallazgos cerrados: **H-02** (Telegraf healthcheck `curl /metrics`), **F-8** (CO₂ gen ASHRAE 4.5), **F-7** (PATCH 007 valve rate limiter), **F-5** (PATCH 008 thermal α heat vs cool), **H-05** (coverage gating CI 80 %, baseline 89.15 %). Suite 198 → **211/211 PASS**. Hallazgos abiertos: **17** (1 alta · 8 media · 8 baja).
- **2026-05-10 17:00** — bloque Should completado — 3 hallazgos finales cerrados: **H-12** (matriz `SPEC_TEST_TRACEABILITY.md` 49 reglas + test estático 4 cases), **H-03** (slowapi rate limiting 10/5/60 per minute, 5 tests), **H-06** (job CI `e2e-stack` que ejecuta `make demo` + captura logs on failure). Suite 211 → **220/220 PASS**. Hallazgos abiertos: **14** (1 alta · 5 media · 8 baja). Único alta restante sigue siendo H-01.

## Fase 11 — Notebooks didácticos y casos de uso explícitos

Tras cerrar la auditoría extrema (fases 1–10), se incorpora una capa docente
explícita: notebooks por caso de uso + documentación web por caso de uso +
contratos extraídos para integradores.

| Sub-fase | Entregable | Estado |
|---|---|---|
| 11.0 | `docs/audit/USE_CASE_MATRIX.md` (10 casos + extra, capas Medallion) | ✅ |
| 11.1 | `docs/audit/NOTEBOOK_PLAN.md` (45 notebooks, niveles, deps) | ✅ |
| 11.2 | `docs/audit/DOCS_REPORT.md` (mapa de la nueva docs/) | ✅ |
| 11.3 | `notebooks/_common/` helpers + `notebooks/_data/` mocks | ✅ |
| 11.4 | 45 notebooks didácticos (3 overview + 42 casos A-J) | ✅ |
| 11.5 | `docs/use-cases/`, `docs/contracts/`, `docs/validation/`, `docs/operations/`, `docs/notebooks/` | ✅ |
| 11.6 | Actualización `mkdocs.yml` con la nueva navegación | ✅ |
| 11.7 | Validación notebooks (JSON, sin secretos, paths relativos) | ✅ |

### Histórico fase 11

- **2026-05-10 09:00** — fase 11 iniciada — exploración de fuentes
  (`docs/archive/CAPTIA_Informe_CasosDeUso_DatosSinteticos.md`,
  `CENTINELA_Guia_Alumnos_v4.md`, `MEDALLION_Arquitectura_Guia_Referencia.md`,
  `docs/specs/synthetic-bms/01-product-spec.md`,
  `02-domain-spec.md`).
- **2026-05-10 09:30** — sub-fase 11.0–11.2 cerradas (auditoría docente).
- **2026-05-10 11:30** — sub-fase 11.3 cerrada (helpers + mocks deterministas).
- **2026-05-10 14:00** — sub-fase 11.4 cerrada (45 notebooks generados con
  18-section template, mocks etiquetados, `seed=42`).
- **2026-05-10 15:00** — sub-fase 11.5 cerrada (28 markdowns nuevos en
  `docs/use-cases/`, `docs/contracts/`, `docs/validation/`, `docs/operations/`,
  `docs/notebooks/`, todos cruzados con specs).
- **2026-05-10 15:30** — sub-fase 11.6 cerrada (`mkdocs.yml` con nueva
  navegación; mantenido `strict: false` por enlaces a código).
- **2026-05-10 16:00** — sub-fase 11.7 cerrada — validación notebooks (JSON
  válido, sin secretos, schema canónico citado, mocks etiquetados).

## Resumen de cobertura final

- **45 notebooks** repartidos en 11 directorios (overview + 10 casos).
- **28 documentos web nuevos** en 5 secciones (`use-cases`, `contracts`,
  `validation`, `operations`, `notebooks`).
- **3 documentos de auditoría docente** (`USE_CASE_MATRIX.md`,
  `NOTEBOOK_PLAN.md`, `DOCS_REPORT.md`).
- Auditoría extrema y auditoría docente cierran 11/11 fases.
