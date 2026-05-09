# Validación de realismo físico

> **Última verificación:** 2026-05-10
> **Reporte detallado:** [`audit/PHYSICAL_REALISM_REPORT.md`](../audit/PHYSICAL_REALISM_REPORT.md).
> **Spec asociada:** `docs/specs/digital-twin-bms-physics-validation/`.

## Score actual

**0.94** (estimado mayo 2026). Top 10 gaps documentados con id `L-PV-XX`.

## Reglas de plausibilidad

Las reglas físicas validan que los datos sintéticos **podrían** existir en
una instalación real:

- **CO₂ rate**: ASHRAE 4.5 ppm/persona/min (cumplido).
- **HVAC anti short-cycle**: min on/off 5 min (PATCH 004 aplicado).
- **Setpoint jitter**: σ ≤ 0.05 °C (PATCH 002).
- **Cooling dehumidification**: ΔT 8 °C entre supply y return (PATCH 003).
- **Valve rate limiter**: máx 1 cambio/3 min (PATCH 007).
- **Thermal α**: ratio heat/cool documentado (PATCH 008).
- **Temperature coupling outdoor↔indoor**: 0.15 (calibración inicial,
  L-01 abierta).

## Patches al vendor

Todos los parches físicos viven en
`vendor/synthetic-generator/PATCHES/NNN-titulo.patch`:

- 002 — setpoint jitter.
- 003 — cooling dehumidification ΔT.
- 004 — HVAC min on/off (anti short-cycle).
- 005 — TZ-aware `datetime.now`.
- 006 — Prometheus doble scrape.
- 007 — valve rate limiter.
- 008 — thermal α heat/cool.

Cada patch tiene tests de regresión. Suite total **211/211 PASS**.

## Cómo se mide el score

Cada regla aporta una fracción al score (0..1). El score global se
recalcula tras aplicar cada patch. La metodología y los tests viven en:

- `docs/specs/digital-twin-bms-physics-validation/04-physical-plausibility-rules.md`
- `docs/specs/digital-twin-bms-physics-validation/05-controlled-simulation-validation.md`
- `docs/specs/digital-twin-bms-physics-validation/08-physical-realism-score.md`
