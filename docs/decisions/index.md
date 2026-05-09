# Decisiones técnicas (ADRs)

> **Última verificación:** 2026-05-10
> **Fuente de verdad:** `docs/specs/synthetic-bms/09-decision-log.md`.

Las decisiones técnicas (ADRs) se mantienen consolidadas en el log SDD. Esta
página actúa como índice navegable. Cada entrada enlaza al ancla
correspondiente del log.

## ADRs aceptadas

| ID | Título | Tópico |
|---|---|---|
| ADR-001 | Vendoring de `synthetic-generator` con workspace `uv` | repo structure |
| ADR-002 | Stack Docker autónomo siguiendo patrón CAPTIA-CONNECT | infra |
| ADR-003 | Microservicio FastAPI control plane | services |
| ADR-004 | Schema canónico CAPTIA inmutable (`captia_point` + 5 tags) | contracts |
| ADR-005 | Topics MQTT `captia/{env}/{tenant}/{site}/{device}/...` | contracts |
| ADR-006 | 7 buckets InfluxDB con retenciones específicas | storage |
| ADR-007 | Frecuencia 5 s telemetría · ≤ 1 min state_events · backfill 365 d | timing |
| ADR-008 | `seed=42` por defecto · `numpy.random.default_rng` | determinism |
| ADR-009 | 10 aulas default · configurable hasta 70 | scale |
| ADR-010 | 4 tipos de fallo HVAC v1 · etiquetados en `state_events` | faults |
| ADR-011 | Grafana provisioning como UI (no UI custom) | ui |
| ADR-012 | Política `.claude/` (subagentes + reglas + ≤ 200 líneas CLAUDE.md) | tooling |
| ADR-013 | Idioma docs en español · identificadores en inglés | language |
| ADR-014 | Pipeline `uv` + `ruff` + `pytest` · Python 3.12 estricto | tooling |
| ADR-015 | Healthchecks obligatorios · tags fijos · `${VAR:-default}` | infra |
| ADR-016 | Vendoring policy: parches en `PATCHES/NNN-titulo.patch` | vendoring |

## ADRs físicas (auditoría)

| ID asociado | Patch vendor | Resumen |
|---|---|---|
| H-23 | `PATCHES/002-setpoint-jitter-configurable.patch` | Jitter setpoint configurable (`setpoint_jitter_std`); override 0.05 reduce 6× los eventos `state_events`. |
| L-PV-09 | `PATCHES/003-humidity-dehumidification.patch` | RH ahora deshumidifica cuando HVAC en cooling. |
| L-PV-07 | `PATCHES/004-hvac-anti-short-cycle.patch` | `hvac_enable` con `_enforce_min_dwell` (5 min on / 5 min off). |

## Cómo registrar una nueva ADR

1. Editar `docs/specs/synthetic-bms/09-decision-log.md` añadiendo:
   ```markdown
   ### ADR-NNN: Título
   - **Context**: razón
   - **Decision**: decisión tomada
   - **Consequences**: impacto y trade-offs
   - **Status**: Accepted | Superseded | Deprecated
   ```
2. Actualizar este índice en `docs/decisions/index.md` con una entrada en la tabla.
3. Si la decisión modifica un contrato (MQTT, schema), actualizar `docs/specs/synthetic-bms/02-domain-spec.md` o `04-infra-spec.md` y propagar tests.
4. Commitear con `docs(decision): ADR-NNN título corto`.
