# Auditoría extrema — Índice

> **Última verificación:** 2026-05-10
> **Estado consolidado:** [STATUS](STATUS.md).
> **Repo de referencia:** `C:\CAPTIA\CAPTIA-CONNECT\captia-connect`.

## Reportes producidos

| Fase | Reporte | Resumen | Estado |
|---|---|---|---|
| 1 | [Mapa del repo](00-repo-map.md) | Árbol exhaustivo con 10 findings iniciales | ✅ |
| 2 | [Matriz de consistencia](CONSISTENCY_MATRIX.md) | BMS ↔ CAPTIA-connect en 11 áreas; top 5 críticas + top 5 aceptables | ✅ |
| 3 | [Plan reestructuración docs](DOCS_RESTRUCTURE_PLAN.md) | MkDocs Material + GitHub Pages; mapa de migración | ✅ |
| 4 | [Reporte top 20](AUDIT_REPORT.md) | 3 alta · 9 media · 8 baja | ✅ |
| 5 | [Validación E2E](E2E_VALIDATION_REPORT.md) | 10 escenarios E2E + 8 físicos PASS contra stack live; +H-21, +H-22 | ✅ |
| 6 | [Realismo físico](PHYSICAL_REALISM_REPORT.md) | Score 0.94; top 10 gaps (F-1..F-10); +H-23 jitter setpoint | ✅ |
| 7 | (correcciones aplicadas — patches 002/003/004) | 3 patches al vendor + 15 tests nuevos pasando, 194/194 suite | ✅ |
| 8 | (este sitio) | Reestructuración `docs/` como web | ✅ |
| 9 | GitHub Pages workflow | despliegue automático | ✅ |
| 10 | [Plan de acción](ACTION_PLAN.md) | priorización MoSCoW; 27 hallazgos abiertos (3 alta · 11 media · 13 baja) + roadmap | ✅ |
| 11 | [Matriz casos uso](USE_CASE_MATRIX.md) · [Plan notebooks](NOTEBOOK_PLAN.md) · [Reporte docs](DOCS_REPORT.md) | 45 notebooks + 28 docs web nuevos | ✅ |
| Cierre | [**Reporte final consolidado**](FINAL_REPORT.md) | snapshot tras 11 fases; stack live; todos los patches/ADRs/reportes/commits | ✅ |
| Re-run | [**Audit re-run 2026-05-10**](AUDIT_RERUN_2026-05-10.md) | post-cierre; detecta + cierra dashboard caseD fail; consolida drift 74 files; 10 servicios live | ✅ |

## Hallazgos consolidados

### Alta severidad

- **H-01** — event payload `ts_ns` vs `ts` ISO 8601 ([AUDIT_REPORT](AUDIT_REPORT.md)).
- **H-02** — Telegraf healthcheck `pgrep` (insuficiente).
- **H-03** — endpoints `/v1/*` sin rate limiting.
- **H-23** — jitter setpoint excesivo (75 ev/h por aula). **Cerrada por PATCH 002**.
- **F-1 / L-PV-09** — humidity cooling no deshumidificaba. **Cerrada por PATCH 003**.
- **F-2 / L-PV-07** — HVAC short-cycling. **Cerrada por PATCH 004**.

### Media severidad

- **H-04** — `telemetry_events` operativo aquí, deprecated upstream.
- **H-05** — sin coverage gating en CI.
- **H-06** — CI no levanta el stack.
- **H-07** — generador host (no contenedor) — depende del entorno (Cloudflare R2 timeout en pull base image).
- **H-08** — schema verify solo local.
- **H-09** — `init_env.sh` no documentado.
- **H-10** — `bms_signal_alias` con 1 test.
- **H-11** — Dependabot abierto.
- **H-12** — physics specs ortogonales (no enlazadas con tests).
- **H-21** — drift TZ runner (vendor `datetime.now()` naive).
- **H-22** — Prometheus target `bms-data-generator` down (host scrape).

### Baja severidad

- **H-13** — Telegraf controller heartbeat (omitido por simplicidad).
- **H-14** — `tagexclude` no aplicado en `captia_cmd_event`.
- **H-15** — MQTT auth ausente (dev-only).
- **H-16** — Python 3.12 ADR no formalizado.
- **H-17** — `.pptx` sin enlazar.
- **H-18** — TODOs query (cache Redis).
- **H-19** — healthchecks no estandarizados.
- **H-20** — contratos sin doc unificado (cubierto por este sitio + matriz).

### Físicos top 10 (PHYSICAL_REALISM_REPORT)

| ID | Resumen | Estado |
|---|---|---|
| F-1 | Humidity cooling no deshumidificaba | ✅ cerrada PATCH 003 |
| F-2 | HVAC short-cycling | ✅ cerrada PATCH 004 |
| F-3 | `relay_1..4` no emitidas como variables independientes | ⚪ baja prioridad |
| F-4 | Jitter setpoint excesivo (= H-23) | ✅ cerrada PATCH 002 |
| F-5 | Cooling/heating con mismo α en thermal model | ⚪ media |
| F-6 | Discontinuidad ruido `occ=0 → 1` | ⚪ baja |
| F-7 | Válvula sin rate limiter | ⚪ media |
| F-8 | CO₂ `gen=7.5` vs ASHRAE 4.5 | ⚪ media (pendiente L-01) |
| F-9 | Iluminancia `target_off=70` lux con persianas | ⚪ baja |
| F-10 | Ocupación entrada/salida instantánea | ⚪ baja |

## Reglas de la auditoría

> **No** declarar éxito sin evidencia (logs, queries, outputs).
> **No** cambiar contratos (MQTT, schema, buckets) sin ADR.
> **No** secretos hardcodeados.
> **No** imágenes Docker `latest`.
> **Cada** corrección produce commit con referencia al hallazgo.
