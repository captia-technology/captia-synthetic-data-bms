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
- **Decisión**: 7 buckets: `telemetry` (14d), `telemetry_1m` (30d), `telemetry_15m` (90d), `telemetry_1h` (365d), `state_events` (90d), `telemetry_events` (90d), `captia_metadata` (∞).
- **Alternativas**: buckets custom (rompe queries pre-existentes).
- **Consecuencias**: 5 tareas Flux activas para downsampling.
- **Estado**: Aceptada (ampliada 2026-05-10 con `telemetry_events` para eventos cmd/ack — vacío en standalone, poblado por controllers en producción).

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

## ADR-019 — Event payload `ts_ns` (BMS standalone) vs ISO `ts` (upstream)

- **Contexto**: la matriz de consistencia
  (`docs/audit/CONSISTENCY_MATRIX.md` row 2 "Payload format") detectó que
  CAPTIA-CONNECT upstream publica eventos con timestamp ISO 8601
  (`"ts": "2026-05-09T18:30:00.123Z"`), mientras BMS publica eventos con
  unix nanoseconds (`"ts_ns": 1715260800000000000`). El segundo
  `[[inputs.mqtt_consumer]]` en `infra/telegraf/telegraf.conf:62-78` usa
  `json_time_key = "ts_ns"` con `json_time_format = "unix_ns"` para AMBOS
  streams (telemetry + event), por lo que un evento ISO de upstream caería
  en el consumer pero no se parsearía y usaría `now()` (drift).
- **Decisión**: **mantener `ts_ns` como contrato BMS-internal** y resolver
  la integración cross-stack vía bridge Telegraf en futura fase de
  integración con CAPTIA-CONNECT.
  - **Por qué `ts_ns` en BMS**: consistente con el flujo telemetry (unix_ns
    es nativo de InfluxDB line protocol), no requiere parsing de strings
    en el publisher (microseconds más eficiente), y todos los tests del
    repo asumen ese formato.
  - **Plan de bridge** (post-v1, integración real): añadir un tercer
    `[[inputs.mqtt_consumer]]` con namepass="captia_cmd_event" y
    `json_time_key = "ts"` + `json_time_format = "2006-01-02T15:04:05.999Z07:00"`
    para topics que vengan exclusivamente de upstream. Esto requiere:
    1. Identificar el sub-namespace (ej: `captia/upstream/...` vs
       `captia/local/...`) o usar `client_id` como discriminador.
    2. Aplicar `processors.rename` para normalizar `ts` → `ts_ns` si fuera
       deseable la convergencia (no requerido para storage en
       InfluxDB — Telegraf interpreta el time field internamente).
    3. ADR específico de integración en momento de hacer la conexión real.
- **Alternativas**:
  - Cambiar BMS a ISO `ts` para alinear con upstream (descartada — rompe
    19+ tests + sinks vendor que producen `ts_ns`; sería un patch al
    vendor con propagación masiva).
  - Telegraf processor que detecte automáticamente formato (descartada —
    `json_time_key` es estático en Telegraf 1.32; no hay auto-detect).
  - Duplicar consumers ahora con namepass distinto (descartada — sin
    integración real es config muerta).
- **Consecuencias**:
  - BMS standalone es 100 % funcional con `ts_ns` (verificado en E2E).
  - Mensaje upstream con ISO `ts` que llegue por accidente al broker BMS
    pierde fidelidad temporal (Telegraf usa `now()`). Esto es aceptable
    para demo y no bloquea el roadmap ML porque BMS no consume eventos
    de upstream en este alcance.
  - Cuando llegue la integración real, este ADR es el punto de partida
    para el bridge. Documentado que la decisión está tomada y los
    detalles del bridge se resuelven en una sub-fase de integración.
- **Estado**: Aceptada (con plan de bridge para integración futura).
- **Cierra**: H-01 (`docs/audit/AUDIT_REPORT.md`), única alta restante
  del ACTION_PLAN.

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

## ADR-020 — Metadata bootstrap automático en cada deploy (replicado de captia-connect)

- **Contexto** (2026-05-10): el bucket `captia_metadata` ya se poblaba via
  `infra/influxdb/init/init_buckets_tasks.sh::populate_metadata` (awk). Pero
  ese parser awk era frágil (no manejaba `derivations.yaml`, no usaba
  `display_name` ES, escribía menos campos que captia-connect). Necesitamos
  que el catálogo se rellene automáticamente desde el primer deploy con
  schema completo y compatible con el patrón captia-connect.
- **Decisión**: nuevo servicio Docker `metadata-bootstrap` (Python) en
  `tools/metadata-bootstrap/`, adaptado de
  `captia-connect/tools/metadata-bootstrap/`. Encadenado tras
  `influx-init` con `condition: service_completed_successfully`.
  `BOOTSTRAP_MODE=force` purga + reescribe en cada deploy. Soporta
  `production_name` (override local) y `derivations.yaml` (12 vars
  adicionales).
- **Alternativas**: (a) mantener parser awk — descartada por fragilidad y
  divergencia con captia-connect; (b) ejecutar bootstrap manualmente
  bajo profile — descartada porque rompe el principio "primer deploy
  completo sin pasos manuales".
- **Consecuencias**: el awk legacy queda como fallback (deprecated). El
  servicio Python tiene precedencia. `make verify-metadata` valida ≥
  N_aulas × 33 entries. El generator y los dashboards downstream pueden
  asumir catálogo poblado.
- **Estado**: Aceptada.

## ADR-021 — Derivations declarativas vendor → production (cierra L-PV-01)

- **Contexto** (2026-05-10): el vendor `synthetic-generator` emite 21
  variables por aula. La spec PPTX `simarro-prod` slide 14 lista 30
  variables canónicas (12 vars adicionales: `temperature-indoor`, `t-voc`,
  `max-sound-level`, `aire`, `aire_state`, `fan_speed_01..03`,
  `fan_speed_03_state`, `light_01..02`, `valve_state`). La regla 003
  prohíbe modificar el vendor. Necesitamos cerrar L-PV-01 sin tocar
  `vendor/synthetic-generator/`.
- **Decisión**: nuevo `config/domains/<dom>/derivations.yaml` con
  declaraciones `name + source + transform + params + metadata`. Nuevo
  módulo `extensions/bms_signal_alias/derivations.py` con 6 transforms
  (`passthrough`, `jitter`, `linear`, `bool_to_speed`,
  `bool_to_intensity`, `threshold_to_bool`). El `AliasSinkAdapter`
  intercepta cada `emit(point)`, computa derived points sobre el name
  vendor, y emite original + derivados al sink real (después del
  rename). Determinismo preservado: RNG seeded por hash de
  `(name, asset, ts_5s_bucket)`.
- **Alternativas**: (a) parchear vendor con nuevos physics — descartada
  por regla 003; (b) sink wrapper externo (no en alias adapter) —
  descartada porque duplica responsabilidades; (c) generar las 12 vars
  desde el host con un script post-MQTT — descartada por latencia y
  duplicación de pipeline.
- **Consecuencias**: emisión por aula pasa de 21 → 33 vars. Telegraf
  consumer y processors absorben sin cambios (mismo measurement
  `captia_point`). `metadata-bootstrap` también lee `derivations.yaml`
  y escribe sus entries a `captia_point_meta` con field
  `source=derivation:<transform>` para distinguir origen. Cierra
  L-PV-01 (BLOCKER) — el generador es ahora drop-in replacement de
  `simarro-prod` con 30/30 vars cubiertas.
- **Estado**: Aceptada.

## ADR-022 — `persistent_session = false` en Telegraf MQTT consumer

- **Contexto** (2026-05-10): debug end-to-end del incidente "Telegraf
  reporta `Wrote batch of N metrics` pero datos no aparecen en bucket".
  Diagnóstico: el queue persistente del broker acumulaba mensajes con
  timestamps corruptos (residuo histórico del bug `date +%s%N` en Alpine
  publisher demo, que enviaba `ts_ns` como 10 dígitos en vez de 19,
  interpretado como año 1970 por Telegraf). Cada restart de Telegraf
  drenaba ese backlog; los puntos quedaban "outside retention policy" y
  se descartaban silenciosamente con HTTP 204 sin error visible.
- **Decisión**: `persistent_session = false` en ambos `mqtt_consumer`
  (telemetry + events). Sin esto, el cliente recibe queue antiguo del
  broker en cada reconnect. También eliminado `agent.statefile` (estaba
  ligado al persistent_session). Subido `max_inflight_messages 200 →
  1000` en Mosquitto como red de seguridad ante futuros bursts.
- **Alternativas**: (a) mantener persistent_session=true y rotar
  `client_id` por restart — funcionaría pero pierde mensajes al rotar
  (cambia QoS1 contract); (b) limpiar manualmente el queue del broker
  tras incidentes — descartada por imposibilidad de detectar el problema
  (silent drops).
- **Consecuencias**: pérdida del comportamiento "QoS1 from-the-last-ack"
  tras restart de Telegraf — aceptable porque el generator vive en el
  mismo stack y los datos perdidos son segundos de retransmisión, no
  horas. Ganancia: 0 silent drops, troubleshooting trivial vía métricas
  Telegraf, recovery time-to-data tras restart < 30s.
- **Estado**: Aceptada.

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
