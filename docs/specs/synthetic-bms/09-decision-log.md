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
- **Decisión**: 4 tipos: `sensor_drift`, `valve_stuck`, `fan_failure`, `refrigerant_low`. Probabilidades configurables vía `config/domains/bms_classrooms/faults.yaml`.
- **Alternativas**: sin fallos (bloquea Caso C); fallos físicos completos LBNL FDD (over-engineering v1).
- **Consecuencias**: hooks abiertos para añadir tipos.
- **Estado**: Aceptada.

## ADR-010-bis — Etiquetas de fallo en `captia_fault_labels` (no `state_events:variable=fault.*`)

- **Contexto**: la decisión inicial (ADR-010 v1) materializaba los eventos
  como series con `variable=fault.<tipo>` dentro del bucket `state_events`,
  pero la guía CENTINELA+ es taxativa al respecto: *"las etiquetas de fallo
  no van en InfluxDB junto a la telemetría canónica: van en lakeFS o en un
  measurement separado `captia_fault_labels`"* (`docs/CENTINELA_Guia_Alumnos_v4.md:464`).
  Mezclarlas con `captia_point` rompería:
  - El contrato tácito *un measurement = un schema de tags*.
  - Cualquier query agregada (ej. `mean(value)` sobre `captia_point` con
    `variable` libre) que sumaría 0/1 lógicos a magnitudes físicas.
  - La auditabilidad — un consumidor del Caso C no sabría distinguir un
    "fallo" de una telemetría real con un nombre engañoso.
- **Decisión**: las etiquetas se publican al bucket `state_events` (90 d
  retención) en el measurement dedicado `captia_fault_labels` con:
  - tags: `captia_env`, `domain_id`, `site_id`, `asset_id`, `fault_type`
  - fields: `active` (0/1), `severity` (0.3–1.0).
- **Consecuencias**:
  - El dashboard `bms_faults_caseC.json` consulta `captia_fault_labels` (no
    `variable =~ /^fault\\..*/`).
  - Documentado en `02-domain-spec.md` (sección *Etiquetado de fallos*).
  - El docstring de `extensions/bms_calibration/src/bms_calibration/faults.py`
    reproduce el contrato.
- **Estado**: Aceptada (sustituye la sub-decisión de ADR-010 sobre routing).

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

## ADR-016 — Vendoring policy: parches en `PATCHES/NNN-titulo.patch`

- **Contexto**: el código en `vendor/synthetic-generator/` es read-only por
  política (ver `.claude/rules/003-vendoring-policy.md`), pero la auditoría
  física descubrió 7 mejoras necesarias (PATCHES 002–008).
- **Decisión**: cualquier modificación al vendor se registra como
  `vendor/synthetic-generator/PATCHES/NNN-titulo.patch` con el formato
  `Title / Status / Applied on / Linked finding / Diff / Validation /
  Reversibility`. Los parches deben ser retrocompatibles (defaults legacy).
- **Alternativas**: editar vendor sin trazabilidad (descartada por imposibilidad
  de re-vendoring posterior); fork del vendor (descartada por overhead).
- **Consecuencias**: `scripts/update_vendor.sh` reaplicará los patches
  automáticamente al sincronizar con upstream. 8 patches aplicados a fecha
  2026-05-10.
- **Estado**: Aceptada.

## ADR-018 — Sin `outputs.heartbeat` Telegraf en BMS standalone

- **Contexto**: el upstream CAPTIA-CONNECT añade un output
  `[[outputs.heartbeat]]` en su `telegraf.conf` que reporta cada N segundos
  el estado del agente a un Telegraf Controller central. La auditoría
  (`docs/audit/CONSISTENCY_MATRIX.md` fila "Variables de entorno") detectó
  que BMS no replica ese output (ver `infra/telegraf/telegraf.conf:6`).
- **Decisión**: BMS standalone **no** incluye `outputs.heartbeat`. Por dos
  razones:
  1. **No hay Telegraf Controller** en el stack BMS — se diseñó como demo
     autónoma (ADR-002). El heartbeat sin destinatario es ruido sin valor.
  2. **El healthcheck del contenedor** (`compose/base.yaml:98-102`,
     `curl /metrics | grep '^# HELP'` desde H-02) ya cubre la observabilidad
     de Telegraf vivo + sirviendo métricas en Prometheus :9273.
- **Alternativas**:
  - Replicar `outputs.heartbeat` apuntando a un Controller dummy
    (descartada — adds dead config, sin valor en demo).
  - Apuntar el heartbeat a un Controller externo (CAPTIA-CONNECT) en modo
    integración (post-v1, requiere ADR específico para flujo cross-stack).
- **Consecuencias**:
  - Si BMS se integra en una instalación con CAPTIA-CONNECT real, hay que
    añadir el output explícitamente (referencia: `modules/ingest/telegraf/telegraf.conf`
    en captia-connect repo).
  - El contenedor `captia-bms-telegraf` se considera healthy si responde
    `/metrics` (cobertura local), no si el Controller central lo ve.
- **Estado**: Aceptada (decisión consciente para demo standalone).
- **Cierra**: H-13 (`docs/audit/AUDIT_REPORT.md`).

## ADR-017 — `telemetry_events` bucket mantenido pese a deprecated upstream

- **Contexto**: la matriz de consistencia (`docs/audit/CONSISTENCY_MATRIX.md`
  fila "Buckets") detectó que CAPTIA-CONNECT upstream deprecó
  `telemetry_events` el 2026-04-02 mientras BMS lo mantiene operativo
  (T-PV-18). Si en producción ambos stacks comparten InfluxDB, BMS escribe
  a un bucket que upstream ya no consume.
- **Decisión**: BMS mantiene `telemetry_events` (90 d retention) porque:
  1. Es la convención del PPTX `influxdb-simarro-buckets.pptx` slide 8 que
     sigue siendo source-of-truth para Simarro.
  2. Telegraf en BMS escribe eventos como `captia_cmd_event` measurement
     que sí necesita un bucket dedicado para retención distinta de
     telemetry continuous.
  3. Cuando upstream confirme path de migración, BMS adopta vía PR explícito
     con migración de datos retenidos.
- **Alternativas**: eliminar el bucket y unir eventos a `telemetry`
  (descartada — distintas retenciones y consultas Flux); duplicar a ambos
  buckets (descartada — doble write innecesario).
- **Consecuencias**: divergencia documentada con upstream. Acción de
  seguimiento: revisar tras próxima sincronización con CAPTIA-CONNECT
  (ver `scripts/update_vendor.sh`).
- **Estado**: Aceptada (con revisión periódica).
- **Cierra**: H-04 (`docs/audit/AUDIT_REPORT.md`).
