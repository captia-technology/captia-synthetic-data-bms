# Auditoría — Reporte síntesis (TOP 20 hallazgos consolidados)

> **Fecha**: 2026-05-09. Comit base: `be2b147` + tests audit incluidos.
> Evidencia procedente de: `00-repo-map.md`, `CONSISTENCY_MATRIX.md`,
> tests automáticos de auditoría (`tests/integration/test_*audit*`,
> `modules/bms-data-generator/tests/integration/test_*e2e*`),
> ejecuciones live contra el stack docker corriendo en local.

## Resumen ejecutivo

| Indicador | Valor |
|---|---|
| Servicios docker `(healthy)` | 8/8 |
| Generator `bms-data-generator` | uvicorn host vivo, job `running` |
| Tests verdes (workspace) | **143 passed**, 0 failed |
| Tests verdes (vendor unit) | **129 passed** |
| Tests audit estáticos | 61 (flux tasks 12 + metadata 8 + scenarios 34 + telegraf routing 7) |
| Lint ruff | All checks passed |
| Schema canónico InfluxDB en producción | ✅ verificado en vivo |
| CI workflows | 3 (`ci`, `release`, `security`) |
| Specs SDD totales | 25 docs (synthetic-bms 14 + physics-validation 11) |
| Imágenes Docker pinned | 9/9 (sin `latest`) |
| Secretos hardcodeados detectables | 0 |
| Paths absolutos de host | 0 |

### Veredicto

**Repo es publicable hoy** con 8 servicios sanos, schema canónico CAPTIA validado live, suite de tests robusta (143 + 129) y CI funcional. Los 20 hallazgos de esta auditoría son mejoras incrementales (rigor de healthcheck, sincronización con upstream, observabilidad) y nada bloquea un primer release `v0.1.0` ni un push a GitHub público.

---

## TOP 20 hallazgos

Ordenados por severidad (Alta → Media → Baja), con evidencia y acción mínima trazable.

### 🔴 ALTA — bloquean interoperabilidad o seguridad

#### H-01 · Event payload `ts_ns` vs `ts` ISO 8601

**Síntoma**. `infra/telegraf/telegraf.conf:75` configura `json_time_key = "ts_ns"` (unix_ns) para ambos consumers (telemetry y events). El upstream `captia-connect` usa `json_time_key = "ts"` con formato `2006-01-02T15:04:05.999Z07:00` para events.

**Impacto**. Si un publisher real CAPTIA-connect envía un mensaje `event` JSON con `ts` ISO al broker BMS, Telegraf no parsea el timestamp y usa `now()`. Datos llegan, fidelidad temporal se pierde silenciosamente.

**Evidencia**. `CONSISTENCY_MATRIX.md` § 2; comparativa por agente Explore.

**Acción mínima**. Añadir un segundo `[[inputs.mqtt_consumer]]` específico para topics `captia/+/+/+/+/event/+` con `json_time_key = "ts"` y `json_time_format = "2006-01-02T15:04:05.999Z07:00"`. Coste: ~30 líneas TOML, sin migración.

**Severidad**: Alta — rompedor de interoperabilidad.

---

#### H-02 · Telegraf healthcheck `pgrep` (proceso vivo) vs `wget :9273/metrics`

**Síntoma**. `compose/base.yaml:99` define healthcheck Telegraf como `pgrep -f telegraf`. Esto sólo verifica que el proceso existe, no que está ingresando datos a InfluxDB.

**Impacto**. Telegraf puede estar corriendo pero con consumer MQTT desconectado, output InfluxDB con 401 persistente, o buffer lleno. El stack reportará `healthy` mientras los datos se pierden silenciosamente.

**Evidencia**. `CONSISTENCY_MATRIX.md` § 7; bug real reproducido durante el bring-up inicial (Telegraf "healthy" con `output 401 Unauthorized` durante minutos).

**Acción mínima**. Cambiar a `CMD-SHELL wget -qO- localhost:9273/metrics | head -c 200 | grep -q internal_mqtt_consumer_messages_received`. Garantiza que /metrics responde y que el consumer está vivo.

**Severidad**: Alta — degradación silenciosa.

---

#### H-03 · Endpoints `/v1/*` sin rate limiting

**Síntoma**. `modules/bms-data-generator/src/bms_data_generator/api/{control,datasets,query}.py` aceptan requests sin throttle. Con `BMS_API_TOKEN` correcto un cliente puede:

- iniciar un job, pararlo, iniciar otro, repeat (DoS contra el runner singleton);
- pedir un export 12 m / case B una y otra vez (saturación I/O y disco);
- bombardear `/v1/query` con queries Flux pesadas hacia InfluxDB.

**Impacto**. DoS posible incluso desde clientes autenticados. Para producción multi-tenant es bloqueador.

**Evidencia**. `00-repo-map.md` § 7 hallazgo #4. Inspección directa de código.

**Acción mínima**. Middleware `slowapi` (FastAPI compat) con `Limiter(key_func=get_remote_address)` y decoradores `@limiter.limit("10/minute")` en `start`, `export`, `query`. Coste: 1 dep + 30 líneas. Configurable por env.

**Severidad**: Alta para producción; aceptable para v0.1 dev si se documenta.

---

### 🟠 MEDIA — afectan calidad operacional o consistencia

#### H-04 · `telemetry_events` operativo en BMS, deprecated upstream

**Síntoma**. `infra/influxdb/init/init_buckets_tasks.sh:71` crea bucket `telemetry_events` (90d). El upstream lo deprecó el 2026-04-02. Si BMS y CAPTIA-connect comparten InfluxDB en producción, BMS escribe en un bucket que upstream ya no consume.

**Impacto**. Divergencia de eventos acumulados; cualquier consumer del upstream no verá los eventos publicados desde BMS.

**Evidencia**. `CONSISTENCY_MATRIX.md` § 4.

**Acción mínima**. Añadir ADR-019 explicando si seguimos creándolo (es nuestro contrato local) o si seguimos al upstream. Documentar en `04-infra-spec.md`.

**Severidad**: Media — explícito vía ADR resuelve la cuestión.

---

#### H-05 · Sin `[tool.coverage]` en `pyproject.toml`

**Síntoma**. Los markers pytest (`unit`, `integration`, `smoke`, `snapshot`, `performance`) están definidos pero no hay configuración de `pytest-cov` ni reporte en CI. Imposible saber el % real.

**Impacto**. Un módulo nuevo puede llegar a `main` con 0 % cobertura sin que CI lo detecte. Específicamente `extensions/bms_signal_alias` sólo tiene 1 test pero el `AliasSinkAdapter` envuelve todos los DataPoints emitidos en producción.

**Evidencia**. `00-repo-map.md` § 7 hallazgo #3.

**Acción mínima**. Añadir `pytest-cov` a `[dependency-groups] dev`, configurar `[tool.coverage.run] source = ["modules", "extensions"]` y `[tool.coverage.report] fail_under = 70`. Generar HTML en CI y subir como artifact.

**Severidad**: Media — debe llegar antes del primer release.

---

#### H-06 · CI no levanta el stack real

**Síntoma**. `.github/workflows/ci.yml` ejecuta `mkdocs build` (en este turno: nada todavía), lint, tests in-process y un `docker compose config --quiet`. **No** levanta los 8 contenedores ni ejecuta los smoke contra ellos.

**Impacto**. Una regresión en `infra/telegraf/telegraf.conf` o `init_buckets_tasks.sh` no falla en CI; sólo se detecta en local. Los 4 bugs reales que aparecieron durante el bring-up (port 9002 ocupado, red compartida, `--host` flag, regex parser) habrían pasado desapercibidos en CI.

**Evidencia**. `00-repo-map.md` § 7 hallazgo #6. Inspección de los workflows.

**Acción mínima**. Añadir job `e2e-smoke` en `ci.yml` con `services` dummy o con un `make demo` simplificado que use sólo imágenes ya cached + un test invariant que `mosquitto_pub` y luego query Influx después de 15s. Coste: ~80 líneas YAML + 5 min CI.

**Severidad**: Media — gap de cobertura CI.

---

#### H-07 · Generator host-mode no es servicio gestionado

**Síntoma**. El microservicio `bms-data-generator` corre como `uvicorn` en background tras `make run-host`. Se mata cuando reinicias la máquina, cierras la sesión SSH, o la terminal donde se lanzó. El usuario nos dijo "el generador esta vivo siempre esta mandando valores" — y razón, debería estarlo.

**Impacto**. UX rota para el caso "stack vivo continuamente". El alumno FP entra al día siguiente y no encuentra datos en Grafana, tiene que repetir el `run-host` manualmente.

**Evidencia**. Issue del usuario en este turno; pull `python:3.12-slim` sigue bloqueado en su red.

**Acción mínima**. Tarea #27 ya creada: `make stream` que arranca uvicorn con `nohup` + escribe PID a `.bms-host.pid`, y `make stop-stream` que mata vía PID. Integración con `make demo` y `make down`.

**Severidad**: Media — issue de UX inmediato.

---

#### H-08 · Schema canónico verificado solo parcialmente en CI

**Síntoma**. `scripts/verify_canonical_schema.sh` valida tags presentes en bucket `telemetry`, pero CI no lo ejecuta porque requiere stack levantado (ver H-06).

**Impacto**. El contrato más importante (5 tags + measurement + value) sólo se verifica manualmente.

**Evidencia**. Inspección del workflow `ci.yml` y el script.

**Acción mínima**. Job CI dependiente del job `e2e-smoke` (H-06) que ejecute el verify_canonical_schema.

**Severidad**: Media.

---

#### H-09 · `init_env.sh` no documentado prominente en QUICKSTART

**Síntoma**. `docs/QUICKSTART.md` indica copiar `.env.example` a `.env`, pero ya tenemos `init_env.sh` que **genera `.env` con secretos aleatorios** automáticamente vía `openssl rand -hex 32`. Un alumno puede copiar el `.env.example` con literal `CHANGE_ME_USE_OPENSSL_RAND` y romper el stack.

**Impacto**. Setup falla silenciosamente la primera vez; el alumno se atasca en troubleshooting.

**Evidencia**. `00-repo-map.md` § 7 hallazgo #9.

**Acción mínima**. Editar `QUICKSTART.md` para que el primer paso sea `make init-env` o `bash scripts/init_env.sh`. `make demo` ya lo hace internamente vía `ENV_GUARD`, pero la doc no lo refleja.

**Severidad**: Media — UX.

---

#### H-10 · Coverage de `bms_signal_alias` insuficiente (1 test)

**Síntoma**. `extensions/bms_signal_alias` introdujo el `AliasSinkAdapter` (T-PV-21) que reescribe **cada** DataPoint emitido en producción. Tiene 1 solo test (`test_alias_sink.py`).

**Impacto**. Si el alias tiene un bug (ej. variable sin `production_name` se cuela con vendor name), todo el flujo MQTT publica nombres incorrectos. Imposible detectar sin smoke real.

**Evidencia**. Conteo en `00-repo-map.md` § 2.2.

**Acción mínima**. Añadir 5 tests más: cobertura de variables sin alias, mapeo total de los 22 entries del catalog, idempotencia (renombrar dos veces da el mismo resultado), errores de sink subyacente, fault paths.

**Severidad**: Media — superficie de fallo grande, cobertura mínima.

---

#### H-11 · Branches dependabot abiertas sin PR visibles

**Síntoma**. `git branch -r` muestra `remotes/origin/dependabot/docker/infra/grafana/grafana/grafana-13.0.1` (y otras) sin PR mergeable visible en GitHub.

**Impacto**. Deuda técnica silenciosa de actualizaciones de dependencias y CVE no aplicados.

**Evidencia**. `00-repo-map.md` § 7 hallazgo #7.

**Acción mínima**. Revisión semanal de PRs de Dependabot; auto-merge para minor/patch en deps no críticas (ya está configurado en `dependabot.yml`).

**Severidad**: Media.

---

#### H-12 · Specs `physics-validation` ortogonales a SDD `synthetic-bms`

**Síntoma**. `docs/specs/digital-twin-bms-physics-validation/` (11 documentos) viven en paralelo a `docs/specs/synthetic-bms/` (14 documentos). No hay enlaces cruzados explícitos. Cuando se actualice una de las dos series, la otra puede quedar desactualizada.

**Impacto**. Drift documental. Físico contradice SDD o viceversa.

**Evidencia**. `00-repo-map.md` § 7 hallazgo #5.

**Acción mínima**. Añadir un anchor en `02-domain-spec.md` que enlace a `physics-validation/01-observed-physical-model.md` y viceversa. Lo absorberá la migración a MkDocs.

**Severidad**: Media.

---

### 🟡 BAJA — mejoras incrementales

#### H-13 · Omisión Telegraf Controller heartbeat

**Síntoma**. `infra/telegraf/telegraf.conf` no declara `[[outputs.heartbeat]]` (eliminado en v0.1 por simplificación). Upstream lo usa para registrar agentes con un controller central.

**Impacto**. Si en el futuro queremos integrar este Telegraf con un controller de CAPTIA, no aparecerá. Para v0.1 standalone es irrelevante.

**Acción mínima**. ADR-020 documentando la decisión consciente. Volver a habilitar bajo flag `TELEGRAF_CONTROLLER_HEARTBEAT_URL`.

**Severidad**: Baja.

---

#### H-14 · `tagexclude` faltante en `captia_cmd_event` output

**Síntoma**. El output InfluxDB `#3` que escribe `captia_cmd_event` no incluye `tagexclude = ["topic", "type"]`. El upstream sí (telegraf.conf upstream línea 296-297).

**Impacto**. El tag raw `topic` (con la URL completa MQTT) persiste como tag en InfluxDB, aumentando la cardinalidad innecesariamente.

**Acción mínima**. Añadir `tagexclude = ["topic", "type"]` al output #3 en `infra/telegraf/telegraf.conf`.

**Severidad**: Baja.

---

#### H-15 · `MQTT_USER` / `MQTT_PASSWORD` no expuestos

**Síntoma**. `.env.example` no expone vars de auth MQTT. Mosquitto opera en `allow_anonymous true` (marcado dev-only).

**Impacto**. Para producción hay que añadir auth a Mosquitto y a Telegraf consumers; hoy no hay placeholders.

**Acción mínima**. Añadir vars comentadas a `.env.example` y `password_file`/`acl_file` opcionales en `infra/mosquitto/mosquitto.conf`.

**Severidad**: Baja (dev) / Alta para producción — ya documentado en `SECURITY.md` hardening checklist.

---

#### H-16 · Python 3.12 mínimo sin ADR

**Síntoma**. `pyproject.toml requires-python = ">=3.12"` sin justificación en `09-decision-log.md`.

**Impacto**. Si CAPTIA-connect (algunos módulos) corre Python 3.10, alumnos no podrán reutilizar código directamente.

**Acción mínima**. ADR-021 confirmando 3.12 (asyncio TaskGroup, type union `int | None`, `dataclass(slots=True)`) — tests no fallan en 3.10 pero código asume features 3.12.

**Severidad**: Baja.

---

#### H-17 · Presentaciones `.pptx` en `docs/` sin enlace

**Síntoma**. `docs/captia-connect-partner-integration.pptx` (742 KB) y `docs/influxdb-simarro-buckets.pptx` (769 KB) sin referencia desde el resto de la documentación.

**Impacto**. Archivos huérfanos en el repo público; no se sabe si son fuente de verdad o referencia.

**Acción mínima**. Mover a `docs/archive/presentaciones/` (`DOCS_RESTRUCTURE_PLAN.md` ya lo prevé). Añadir `archive/index.md` con enlace.

**Severidad**: Baja — UX docs.

---

#### H-18 · 2 TODOs activos en `query_service.py` (Redis cache)

**Síntoma**. `services/query_service.py:188` documenta TODO para Redis cache (parte del Dashboard Adapter contract).

**Impacto**. Sin cache, queries idénticas golpean InfluxDB cada vez. Para 5-10 dashboards Grafana con auto-refresh 10s, eso son ~3000 queries/min.

**Acción mínima**. Spec `06-api-and-ui-spec.md` ya lo cita; abrir issue/spec follow-up para v0.2 con: clave `sha256(flux)`, TTL 30s, contador Prometheus de hit/miss.

**Severidad**: Baja para v0.1.

---

#### H-19 · Healthchecks Telegraf y otros

**Síntoma**. Resumen consolidado de healthchecks por servicio:

| Servicio | Healthcheck | Severidad |
|---|---|---|
| mosquitto | mosquitto_sub uptime | OK |
| influxdb | curl /health | OK |
| redis | redis-cli ping | OK |
| telegraf | **pgrep -f telegraf** | ⚠ ver H-02 |
| grafana | curl /api/health | OK |
| prometheus | wget /-/healthy | OK |
| loki | wget /ready | OK |
| promtail | (none, intencional sidecar) | OK |
| bms-data-generator | curl /healthz | OK |

**Acción mínima**. La de Telegraf (H-02) es la única acción.

**Severidad**: Baja (excepto H-02).

---

#### H-20 · Variables `{captia_env, domain_id, site_id, asset_id, variable}` no documentadas como contratos en una sola página

**Síntoma**. La spec del schema canónico está repartida entre `02-domain-spec.md`, `04-infra-spec.md`, `00-research-report.md`, `CENTINELA_Guia_Alumnos_v4.md`. No hay un único lugar oficial.

**Impacto**. Un alumno o consumer externo necesita 4 archivos para entender el contrato. Documentación duplicada con riesgo de drift.

**Acción mínima**. Crear `docs/contracts/{mqtt-topics,payload-format,influx-schema}.md` (ya previsto en `DOCS_RESTRUCTURE_PLAN.md`). Cada uno con:

- Definición formal del contrato.
- Ejemplo válido + ejemplo inválido.
- Test que verifica el contrato.
- Versión / cambios históricos.

**Severidad**: Baja (resuelve con la migración a MkDocs).

---

## Hallazgos cerrados durante esta auditoría

Durante el trabajo previo de los gaps CENTINELA+ ya cerramos varios items:

| Hallazgo previo | Cerrado en commit | Estado |
|---|---|---|
| `telemetry` retention 14 d (era ∞) | `85d3166` | ✅ |
| `captia_metadata` poblado (vacío → 21 vars) | `85d3166` + `c306e45` | ✅ |
| Etiquetas fault en measurement separado | `85d3166` + `67402e8` | ✅ |
| `/v1/query` Dashboard Adapter contract | `c6b8452` | ✅ |
| E2E real Caso A live mode | `b348027` | ✅ |
| Tag `stat=last` en `state_events` | `c23e8e4` | ✅ |
| AliasSinkAdapter T-PV-21 | `c306e45` | ✅ |
| FaultEventEmitter T-PV-22 | `67402e8` | ✅ |
| `downsample_state_1m` lee `captia_point_state` | `c306e45` | ✅ |
| Tests audit estáticos (61 tests) | `be2b147` | ✅ |

## Estado de la suite de tests al cierre

```
pytest -m unit                        →  46 passed
pytest -m integration (workspace)     →  78 passed (incluye 61 audit + 17 API)
pytest -m snapshot                    →   1 passed (FaultInjector seed=42)
pytest vendor unit                    → 129 passed
ruff check + format --check           →  All checks passed
make smoke (4 checks)                 →  4/4 OK
```

Total tests verdes: **143 + 129 = 272**.

## Conclusión

El repo está en estado **publicable con plan de mejoras documentado**. Los 3 hallazgos de severidad alta son arreglables con cambios localizados (≤ 30 líneas cada uno). Los 9 de severidad media se distribuyen entre coverage, CI, observabilidad y documentación. Los 8 de severidad baja son polish.

Todo el trabajo restante está priorizado en `ACTION_PLAN.md` (siguiente entregable).
