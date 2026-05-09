# 09 — Decision log (ADRs ligeras)

> Formato: ID, título, contexto, decisión, alternativas consideradas, consecuencias, estado.

## ADR-001 — Vendoring de `synthetic-generator` en `vendor/`

- **Contexto**: necesitamos reutilizar el generador hexagonal de `tools/synthetic-generator` de CAPTIA-CONNECT sin git submodule (drift) ni dependencia editable (path absoluto frágil).
- **Decisión**: copia controlada en `vendor/synthetic-generator/` como miembro del workspace `uv`.
- **Alternativas**: git submodule (descartada por drift), pip install editable con path absoluto (descartada por fragilidad).
- **Consecuencias**: parches deben registrarse en `vendor/synthetic-generator/PATCHES/`; re-vendoring vía `scripts/update_vendor.sh`.
- **Estado**: Aceptada.

## ADR-002 — Stack Docker autónomo

- **Contexto**: el repo debe ser demo-able sin requerir CAPTIA-CONNECT corriendo.
- **Decisión**: incluir mosquitto + telegraf + influxdb + redis + grafana + prometheus + loki + promtail + generator en compose propio.
- **Alternativas**: solo generator que se conecte a captia-network de CAPTIA-CONNECT (descartada por dependencia externa).
- **Consecuencias**: superficie operacional mayor, pero independencia total.
- **Estado**: Aceptada.

## ADR-003 — Microservicio FastAPI control plane

- **Contexto**: necesitamos endpoints HTTP para control remoto y consulta de estado.
- **Decisión**: FastAPI module `bms-data-generator` que expone `/v1/control`, `/v1/datasets`, `/healthz`, `/readyz`, `/metrics`.
- **Alternativas**: CLI-only (descartada porque no permite control remoto), sin wrapper (descartada por acoplamiento al CLI vendorizado).
- **Consecuencias**: mantener compatibilidad FastAPI/Uvicorn; alineado con dashboard-adapter de CAPTIA-CONNECT.
- **Estado**: Aceptada.

## ADR-004 — Schema canónico CAPTIA exacto

- **Contexto**: compatibilidad con Telegraf de CAPTIA-CONNECT.
- **Decisión**: measurement `captia_point` + 5 tags + field `value` (float).
- **Alternativas**: schema custom (rompe contrato CAPTIA).
- **Consecuencias**: ninguna libertad para cambios; `tests/integration/test_canonical_schema.py` valida.
- **Estado**: Aceptada.

## ADR-005 — Topics MQTT exactos

- **Contexto**: replicar Telegraf consumer pattern de `modules/ingest/telegraf/telegraf.conf`.
- **Decisión**: `captia/{env}/{tenant}/{site}/{device}/telemetry/{name}` y `.../event/{name}`.
- **Alternativas**: topics planos (descartada por incompatibilidad).
- **Consecuencias**: patrón inmutable.
- **Estado**: Aceptada.

## ADR-006 — Buckets InfluxDB replicados

- **Contexto**: replicar `modules/data-plane/scripts/init_influx_buckets_tasks.sh`.
- **Decisión**: 6 buckets: `telemetry` (14d), `telemetry_1m` (30d), `telemetry_15m` (90d), `telemetry_1h` (365d), `state_events` (90d), `captia_metadata` (∞).
- **Alternativas**: buckets custom (rompe queries pre-existentes).
- **Consecuencias**: 5 tareas Flux activas para downsampling.
- **Estado**: Aceptada.

## ADR-007 — Frecuencia 5 s telemetry, backfill default 30 días

- **Contexto**: cubrir Caso A (vivo) y Caso B (predicción 6-12 meses) con un solo modelo de scheduling.
- **Decisión**: 5 s telemetry raw; agregaciones automáticas vía Telegraf/InfluxDB tasks; backfill default 30 días, configurable hasta 365.
- **Alternativas**: 1 min default (insuficiente para Caso A live demo).
- **Consecuencias**: backfill 12 meses produce ~2M puntos/aula (manejable con chunking).
- **Estado**: Aceptada.

## ADR-008 — `seed=42` por defecto, `numpy.random.default_rng`

- **Contexto**: determinismo replicable.
- **Decisión**: `seed=42` configurable vía `BMS_SEED`; usar `np.random.default_rng(seed)` (no `np.random.seed()`).
- **Alternativas**: `np.random.seed()` (descartada por estado global, no thread-safe).
- **Consecuencias**: tests snapshot producen hash idéntico.
- **Estado**: Aceptada.

## ADR-009 — 10 aulas default, configurable hasta 70

- **Contexto**: volumen demo manejable; el dominio existente soporta 70 vía `N_AULAS`.
- **Decisión**: default `BMS_N_AULAS=10`.
- **Alternativas**: 70 fijas (overhead innecesario para demo).
- **Consecuencias**: configs scenario sobrescriben.
- **Estado**: Aceptada.

## ADR-010 — 4 tipos de fallos HVAC v1

- **Contexto**: Caso C requiere etiquetas de fallo; sin docs de catalogación específica.
- **Decisión**: 4 tipos: `sensor_drift`, `valve_stuck`, `fan_failure`, `refrigerant_low`. Probabilidades configurables vía `config/domains/bms_classrooms/faults.yaml`. Etiquetas en bucket `state_events` con `variable=fault.<tipo>`.
- **Alternativas**: sin fallos (bloquea Caso C); fallos físicos completos LBNL FDD (over-engineering v1).
- **Consecuencias**: hooks abiertos para añadir tipos.
- **Estado**: Aceptada.

## ADR-011 — Grafana provisionado, sin UI custom

- **Contexto**: alcance v1 limitado.
- **Decisión**: dashboards Grafana versionados en `infra/grafana/dashboards/*.json`.
- **Alternativas**: UI React custom (descartada por alcance).
- **Consecuencias**: dependencia de Grafana 11.4.
- **Estado**: Aceptada.

## ADR-012 — `.claude` con subagentes especializados

- **Contexto**: alineación con `SKILLS-GOVERNANCE.md` de CAPTIA-CONNECT, evitar `CLAUDE.md` monolítico.
- **Decisión**: 6 subagentes en `.claude/agents/`, 5 reglas en `.claude/rules/`, `CLAUDE.md` ≤ 200 líneas.
- **Alternativas**: `CLAUDE.md` único (no escalable).
- **Consecuencias**: cambios en reglas requieren ADR.
- **Estado**: Aceptada.

## ADR-013 — Idioma: docs en español, código en inglés

- **Contexto**: alineación con docs/ existentes y preferencia jaime.sendra@captiatechnology.com.
- **Decisión**: ver `.claude/rules/005-language-policy.md`.
- **Alternativas**: inglés total (rompe alineación con docs/).
- **Consecuencias**: testing depende de strings de error en español si se valida UI.
- **Estado**: Aceptada.

## ADR-014 — `uv` + `ruff` + `pytest`, Python 3.12 estricto

- **Contexto**: patrón CAPTIA-CONNECT (`modules/dashboard-adapter`, `modules/events-engine`).
- **Decisión**: workspace `uv`, ruff target py312 line-length 100, pytest asyncio_mode auto, markers en pyproject raíz.
- **Alternativas**: poetry, pip-tools (no usados en repo padre).
- **Consecuencias**: `uv.lock` comprometido para reproducibilidad.
- **Estado**: Aceptada.

## ADR-015 — Healthchecks obligatorios; tags fijos; `${VAR:-default}`

- **Contexto**: patrón CAPTIA-CONNECT (`compose/base.yaml`).
- **Decisión**: ver `.claude/rules/004-docker-compose-conventions.md`.
- **Alternativas**: tags `latest` (no permitido).
- **Consecuencias**: `infra-reviewer` valida en CI.
- **Estado**: Aceptada.
