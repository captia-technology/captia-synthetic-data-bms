# 00 — Informe de investigación (read-only, congelado)

> **Fecha**: 2026-05-09. Fuentes: documentos en `docs/`, módulo `C:\CAPTIA\CAPTIA-CONNECT\captia-connect\tools\synthetic-generator`, infraestructura `C:\CAPTIA\CAPTIA-CONNECT\captia-connect\compose\*` y `modules\*`.
> Este documento congela el estado de la investigación realizada durante la fase de planificación. No se modifica salvo errores fácticos.

## 1. Mapa de documentos `docs/`

| Documento | Ruta | Líneas | Propósito | Audiencia |
|-----------|------|-------:|-----------|-----------|
| Informe Casos de Uso Datos Sintéticos | `docs/CAPTIA_Informe_CasosDeUso_DatosSinteticos.md` | 281 | Solicitud formal a CAPTIA Technology de datos sintéticos / anonimizados para 11 casos de uso educativos (mayo 2026). Define necesidades, variables, desafíos y propone generador parametrizable. | Equipo docente IES Simarro → Jaume (CAPTIA Technology) |
| Guía CENTINELA+ alumnos v4 | `docs/CENTINELA_Guia_Alumnos_v4.md` | 908 | Guía integral de arquitectura CENTINELA+: cómo funcionan sensores, MQTT, Telegraf, InfluxDB con schema canónico CAPTIA. Define flujo IoT real, estructura de datos y mapeos de ingesta por caso de uso. | Estudiantes; equipos implementadores |
| Arquitectura Medallion guía referencia | `docs/MEDALLION_Arquitectura_Guia_Referencia.md` | 272 | Patrón Medallion (bronce → plata → oro) aplicado a CENTINELA+. Variantes: estricto, distribuido, híbrido. | Arquitectos técnicos |
| Partner integration | `docs/captia-connect-partner-integration.pptx` | n/a (PPTX) | Presentación de integración con partners. No parseado en esta fase. | Ejecutivos; integradores |
| InfluxDB Simarro buckets | `docs/influxdb-simarro-buckets.pptx` | n/a (PPTX) | Presentación de buckets InfluxDB en simarro-prod. No parseado en esta fase. | Arquitectos datos; DevOps |

## 2. Definición de BMS

**BMS = Building Management System** (Sistema de Gestión de Edificio), no Battery Management System.

Cita textual (`docs/CENTINELA_Guia_Alumnos_v4.md:59`):

> "**Gateway BMS** (Building Management System): el dispositivo principal de control. Publica cada 5 segundos: temperatura interior (`temperature_01`), humedad relativa (`relative-humidity`), CO2 en ppm (`co2`), Compuestos Organicos Volatiles (`t-voc`), indice IAQ (`iaq-index`), nivel de ruido (`avg-sound-level`, `max-sound-level`), luminosidad en lux (`luminosity`), presencia/ocupacion (`occupancy`, `people-count`), consumo electrico (`power_01`), estado y control de climatizacion (`ac_state`, `ac_control`, `fan_speed_01/02/03`, `light_01/02`, `valve_control`, `valve_state`)."

Es el dispositivo IoT que recopila telemetría de aulas educativas (edificios inteligentes en contexto académico).

## 3. Requisitos funcionales detectables

| ID | Requisito | Cita textual | Fuente |
|----|-----------|--------------|--------|
| RF-01 | Proporcionar dump InfluxDB con datos sintéticos / anonimizados de 6-12 meses | "dump de InfluxDB restaurable con `influx restore`, o fichero de line protocol importable con `influx write`" | `docs/CAPTIA_Informe_CasosDeUso_DatosSinteticos.md:169` |
| RF-02 | Datos en bucket `telemetry_1h` como mínimo (bucket principal ML) | "Este es el bucket principal para entrenar modelos. Tiene 1 año de historia." | `docs/CENTINELA_Guia_Alumnos_v4.md:232` |
| RF-03 | Schema canónico CAPTIA: measurement `captia_point`, 5 tags, field `value` | "captia_point,captia_env=prod,domain_id=bms_classrooms,site_id=ies_simarro,asset_id=AULA01,variable=co2 value=712" | `docs/CENTINELA_Guia_Alumnos_v4.md:175` |
| RF-04 | Variables mínimas: `power_01`, `temperature_outdoor`, `solar_irradiance`, `occupancy`, `ac_state`, `fan_speed_XX_state` | "Las variables mínimas necesarias para los casos B, C y D" | `docs/CAPTIA_Informe_CasosDeUso_DatosSinteticos.md:164` |
| RF-05 | Discriminar señales continuas (telemetry) de on-change (state_events) | "Routing: continuo → telemetry / on-change → state_events" | `docs/CENTINELA_Guia_Alumnos_v4.md:36` |
| RF-06 | Poblamiento de `captia_metadata` con rango_min, rango_max, metric_kind, unidad | "captia_metadata poblado para todas las variables" | `docs/CENTINELA_Guia_Alumnos_v4.md:549` |
| RF-07 | Variabilidad realista: ciclos diarios, semanales, estacionales | "Variabilidad real: ciclos diarios, ciclos semanales, diferencias entre períodos lectivos y vacaciones" | `docs/CAPTIA_Informe_CasosDeUso_DatosSinteticos.md:52` |
| RF-08 | Correlaciones básicas (T_ext → T_int, ocupación → CO2) | "Si el dataset sintético incluye estas correlaciones básicas (consumo sube cuando sube la temperatura en verano)" | `docs/CAPTIA_Informe_CasosDeUso_DatosSinteticos.md:52` |
| RF-09 | Etiquetas de fallo para Caso C (anomalías HVAC) | "Fundamental: etiquetas de eventos de fallo" | `docs/CAPTIA_Informe_CasosDeUso_DatosSinteticos.md:68` |
| RF-10 | Documentación de caracterización de variables | Tabla "Información que necesitamos" con rangos, velocidades, correlaciones | `docs/CAPTIA_Informe_CasosDeUso_DatosSinteticos.md:186-195` |
| RF-11 | Generador parametrizable reutilizable (Python) | "implementar un generador de datos sintéticos reutilizable" | `docs/CAPTIA_Informe_CasosDeUso_DatosSinteticos.md:217` |
| RF-12 | Formato entrega: CSV o line protocol directo a InfluxDB | "que cada equipo pueda restaurarlo en su instancia local con un comando" | `docs/CAPTIA_Informe_CasosDeUso_DatosSinteticos.md:170` |

## 4. Requisitos no funcionales detectables

| ID | Categoría | Requisito | Cita / implicación |
|----|-----------|-----------|-------------------|
| RNF-01 | Rendimiento | Ingesta a máxima velocidad sin sleep entre filas | `docs/CENTINELA_Guia_Alumnos_v4.md:399` "Sin sleep — publicar a la máxima velocidad posible" |
| RNF-02 | Confiabilidad | QoS 1 (al menos una entrega) en MQTT | `docs/CENTINELA_Guia_Alumnos_v4.md:85` |
| RNF-03 | Determinismo | Timestamps en nanosegundos epoch consistentes | `docs/CENTINELA_Guia_Alumnos_v4.md:319` |
| RNF-04 | Observabilidad | Trazabilidad MLflow + tag lakeFS de dataset | `docs/CENTINELA_Guia_Alumnos_v4.md:813` |
| RNF-05 | Seguridad | Tokens read-only para Simarro y ITI (no write) | `docs/CAPTIA_Informe_CasosDeUso_DatosSinteticos.md:256` |
| RNF-06 | Reproducibilidad | Dataset versionado en lakeFS con commit/tag | `docs/MEDALLION_Arquitectura_Guia_Referencia.md:40` |
| RNF-07 | Integridad | Validación de rangos físicos | `docs/CENTINELA_Guia_Alumnos_v4.md:541-544` |
| RNF-08 | Escalabilidad | Soportar mínimo 5-10 edificios educativos | `docs/CENTINELA_Guia_Alumnos_v4.md:436` |
| RNF-09 | Completitud | Registros esperados vs reales verificados | `docs/CENTINELA_Guia_Alumnos_v4.md:536` |
| RNF-10 | Consistencia | 5 tags presentes y consistentes en todos los datos | `docs/CENTINELA_Guia_Alumnos_v4.md:548` |
| RNF-11 | Operabilidad | Healthchecks, tags fijos Docker, `${VAR:-default}` | Patrón `C:\CAPTIA\CAPTIA-CONNECT\captia-connect\compose\base.yaml` |
| RNF-12 | Calidad | Sin secretos hardcodeados, ruff/pytest CI-ready | `pyproject.toml` raíz CAPTIA-CONNECT |

## 5. Decisiones técnicas declaradas en docs

| Decisión | Detalle | Fuente |
|----------|---------|--------|
| TSDB: InfluxDB 2.7 | Selector automático de bucket por rango temporal | `docs/CENTINELA_Guia_Alumnos_v4.md:39` |
| MQTT + Mosquitto | Broker dockerizado en servidor edge Simarro | `docs/CENTINELA_Guia_Alumnos_v4.md:74-86` |
| Telegraf | Agente ingesta MQTT → InfluxDB | `docs/CENTINELA_Guia_Alumnos_v4.md:88-127` |
| Measurement único: `captia_point` | Variable identificada por tag, no por field name | `docs/CENTINELA_Guia_Alumnos_v4.md:141-147` |
| Field único: `value` (float) | Estados booleanos como `1.0`/`0.0` | `docs/CENTINELA_Guia_Alumnos_v4.md:147` |
| 5 tags indexados | `captia_env`, `domain_id`, `site_id`, `asset_id`, `variable` | `docs/CENTINELA_Guia_Alumnos_v4.md:149-157` |
| 9 buckets con retenciones | `telemetry` (14d), `_1m` (30d), `_15m` (90d), `_1h` (365d), `state_events` (90d), `captia_metadata` (∞) + downsampling tasks Flux | `docs/CENTINELA_Guia_Alumnos_v4.md:38-50` |
| `metric_kind` dirige downsampling | analog_gauge (mean/min/max), bool_presence (duty/count_rise/last), counter (sum), bool_state (last, count_rise), setpoint_step (last) | `docs/CENTINELA_Guia_Alumnos_v4.md:282-290` |
| Arquitectura Medallion | Bronce (datasets públicos) → Plata (InfluxDB schema CAPTIA) → Oro (features ML / embeddings RAG) | `docs/MEDALLION_Arquitectura_Guia_Referencia.md:6-20` |
| Variante Medallion híbrida | Trabajo distribuido semanas 1-2 + consolidación centralizada semanas 3-4 | `docs/MEDALLION_Arquitectura_Guia_Referencia.md:156-172` |
| Redis caching | Dashboard Adapter cachea queries InfluxDB en Redis | `docs/CENTINELA_Guia_Alumnos_v4.md:47` |
| Grafana dashboards | Visualización vía Dashboard Adapter (REST), no directo a InfluxDB | `docs/CENTINELA_Guia_Alumnos_v4.md:52-53` |
| Variables de entorno (.env) | Nunca hardcodear credenciales | `docs/CENTINELA_Guia_Alumnos_v4.md:345-365` |

## 6. Glosario de dominio

| Término | Definición |
|---------|-----------|
| **BMS** | Building Management System — gateway de control que recopila telemetría de edificios |
| **CENTINELA+** | Sistema real de CAPTIA en producción: IoT edge → MQTT → Telegraf → InfluxDB con schema canónico |
| **AULA01** | Aula de prueba IES Simarro; `asset_id` de referencia |
| **IES Dr. Lluís Simarro** | Centro educativo Valencia/Xàtiva; partner de CAPTIA para CENTINELA+ |
| **CAPTIA schema canónico** | measurement `captia_point` + 5 tags + field `value`; capa plata |
| **Capa Bronce** | Datos crudos en origen (CSV, JSON, MQTT payload); sin transformar |
| **Capa Plata** | Datos normalizados en InfluxDB con schema CAPTIA |
| **Capa Oro** | Datos enriquecidos: features ML, embeddings RAG, indicadores de calidad |
| **Telegraf** | Agente ingesta InfluxData; procesa MQTT, extrae tags, encamina a buckets |
| **state_events** | Bucket de señales on-change (discretas con transiciones documentadas) |
| **telemetry_1h** | Bucket 365 días, resolución 1h; principal para ML |
| **metric_kind** | Metadato que clasifica variable (analog_gauge, bool_presence, counter, bool_state, setpoint_step) |
| **IAQ** | Indoor Air Quality — índice calidad aire interior |
| **HVAC** | Heating, Ventilation, Air Conditioning — climatización |
| **ERA5** | Reanálisis climático ECMWF (Tª, radiación, precipitación global) |
| **BDG2** | Building Data Genome 2 — dataset 53M+ registros edificios educativos |
| **LBNL FDD** | Fault Detection & Diagnosis dataset Lawrence Berkeley con fallos HVAC etiquetados |
| **LakeFS** | Sistema de versionado de datos para datasets bronce |
| **MLflow** | Plataforma MLOps tracking experimentos |

## 7. Mapa del módulo de referencia `tools/synthetic-generator`

### 7.1 Identidad

- Paquete: `synthetic-generator` v0.1.0.
- Ruta: `C:\CAPTIA\CAPTIA-CONNECT\captia-connect\tools\synthetic-generator`.
- Comandos CLI: `run`, `generate`, `stream`, `list-domains`, `validate`.

### 7.2 Stack

- Python ≥ 3.10 (recomendado 3.12).
- Dependencias: `numpy>=1.24`, `pandas>=2.0`, `pydantic>=2.0`, `pyyaml>=6.0`, `paho-mqtt>=2.0`, `tqdm>=4.66`.
- Build: hatchling.

### 7.3 Arquitectura hexagonal (verificado)

```
src/synthetic_generator/
├── core/        # Núcleo zero-deps (config, models, runner, clock, validator, anomalies, rate, pv)
├── ports/       # Protocols (DomainAdapterPort, SinkAdapterPort)
├── domains/     # Adapters de dominio: bms_classrooms, industrial_refrigeration, discrete_manufacturing
└── sinks/       # Adapters de salida: file, mqtt, stdout, null, composite
```

**Reglas de import detectadas**: `core/` no importa `domains/` ni `sinks/`. `domains/` y `sinks/` implementan `ports/`. `cli.py` orquesta vía registry global con decorador `@register_domain`.

### 7.4 Dominio `bms_classrooms` (clave para v1)

- 70 aulas (`AULA01..AULA70`), 16-21 variables por aula.
- Módulos físicos: `environment.py` (Tª exterior, daylight), `indoor.py` (Tª, CO2, humedad), `occupancy.py` (Poisson + horario), `actuators.py` (HVAC, válvulas), `energy.py` (kWh).
- Variable `N_AULAS` (env) override del número de aulas.

### 7.5 Sinks disponibles

| Sink | Archivo | Config | Topic / formato |
|------|---------|--------|-----------------|
| MQTT | `sinks/mqtt.py` | `MQTTSinkConfig(broker_url, qos, client_id, captia_env, captia_tenant, captia_site)` | `captia/{env}/{tenant}/{site}/{device}/telemetry/{name}` JSON `{"value":X,"ts_ns":N}` |
| File | `sinks/file.py` | `FileSinkConfig(path, format)` | csv_long / csv_wide / jsonl |
| Stdout | `sinks/stdout.py` | sin config | JSON por línea |
| Null | `sinks/null.py` | sin config | counter only (test) |
| Composite | `sinks/composite.py` | lista de sinks | múltiples en serie |

### 7.6 Determinismo

- `numpy.random.default_rng(seed)` (NO `np.random.seed()`).
- `seed=42` por defecto.
- `FakeClock` testeable.
- Markers `@pytest.mark.snapshot` para regresión.

### 7.7 Health/metrics existentes

`health.py` expone:
- `/health`, `/metrics`, `/metrics/json`, `/`.
- Métricas Prometheus: `captia_generator_messages_published_total`, `_publish_errors_total`, `_points_generated_total`, `_cycles_completed_total`, `_dataset_regenerations_total`, `_last_publish_duration_ms`, `_connected`, `_current_batch_size`, `_uptime_seconds`, `_messages_by_topic_total`.

## 8. Mapa de infraestructura CAPTIA-CONNECT

### 8.1 Compose layout (verificado)

- `compose/base.yaml`: 6 servicios persistentes (mosquitto, influxdb, redis, telegraf, dashboard-adapter, grafana).
- `compose/observability.yaml`: prometheus, loki, promtail, tempo, otel-collector.
- `compose/edge-standalone.yaml`, `compose/events-engine.yaml`, `compose/synthetic-multi.yaml`, etc.

### 8.2 Servicios y versiones

| Servicio | Imagen | Puerto interno | Healthcheck |
|----------|--------|---------------|-------------|
| Mosquitto | `eclipse-mosquitto:2.0.18` | 1883, 9001 (WS) | `mosquitto_sub` test |
| InfluxDB | `influxdb:2.7` | 8086 | `curl /health` |
| Redis | `redis:7-alpine` | 6379 | `redis-cli ping` |
| Telegraf | `telegraf:1.32` | 9273 (metrics) | `pgrep telegraf` |
| Grafana | `grafana/grafana:11.4` (build local) | 3000 | `curl /api/health` |
| Prometheus | `prom/prometheus:v2.49.1` | 9090 | `wget /-/healthy` |
| Loki | `grafana/loki:2.9.4` | 3100 | `wget /ready` |
| Promtail | `grafana/promtail:2.9.4` | n/a | n/a |

### 8.3 Topics MQTT confirmados

- Telemetría: `captia/{env}/{tenant}/{site}/{device}/telemetry/{name}`.
- Eventos: `captia/{env}/{tenant}/{site}/{device}/event/{name}`.
- Legacy: `captia/sniper/event` (sólo telegraf).

### 8.4 Buckets InfluxDB confirmados

| Bucket | Retención | Origen |
|--------|-----------|--------|
| `telemetry` | 14 días | Live raw |
| `telemetry_1m` | 30 días | Tarea Flux `downsample_1m.flux` |
| `telemetry_15m` | 90 días | Tarea Flux `downsample_15m.flux` |
| `telemetry_1h` | 365 días | Tarea Flux `downsample_1h.flux` |
| `state_events` | 90 días | On-change dedup vía Telegraf statefile |
| `captia_metadata` | infinito | Catálogo variables |

### 8.5 Telegraf config crítica

- Input MQTT: `tcp://${MQTT_HOST}:${MQTT_PORT}`, topics `captia/+/+/+/+/telemetry/+` → measurement `captia_point`.
- Input MQTT eventos: topics `captia/+/+/+/+/event/+` + `captia/sniper/event` → measurement `captia_cmd_event`.
- Output: InfluxDB 2.x a `${INFLUXDB_URL}/api/v2/write` con token/org/bucket.
- Tags extraídos vía regex: `domain_id`, `site_id`, `asset_id`, `variable`, `captia_env`.
- Statefile dedup en `/var/lib/telegraf/statefile`.

### 8.6 Convenciones del repo padre

- Python ≥ 3.12 estricto.
- `uv` package manager.
- `ruff` (target py312, line-length 100).
- `pytest` con `asyncio_mode = "auto"`, markers (`integration`, `performance`, `concurrency`).
- Layout `src/<package_name>/` por módulo.
- Naming: snake_case packages, kebab-case directorios.

## 9. Patrones reusables identificados

| Necesidad | Fuente CAPTIA-CONNECT | Cómo aplicar en BMS |
|-----------|----------------------|--------------------|
| Dockerfile multi-stage | `modules/dashboard-adapter/Dockerfile` | Plantilla para `modules/bms-data-generator/Dockerfile` |
| pyproject módulo | `modules/dashboard-adapter/pyproject.toml` | Plantilla con FastAPI, Pydantic, prometheus-client |
| Compose service | `compose/base.yaml:dashboard-adapter` (líneas 165-244) | Plantilla con healthcheck, depends_on, env vars, mem_limit |
| `.claude` governance | `.claude/SKILLS-GOVERNANCE.md` | Adaptado a `.claude/rules/` |
| Telegraf regex | `modules/ingest/telegraf/telegraf.conf` | Copiar literal a `infra/telegraf/telegraf.conf` |
| Init InfluxDB | `modules/data-plane/scripts/init_influx_buckets_tasks.sh` | Copiar a `infra/influxdb/init/` |
| Tareas Flux | `modules/data-plane/tasks/*.flux` | Copiar 5 archivos a `infra/influxdb/tasks/` |

## 10. Riesgos y observaciones

1. **Vendor drift**: si CAPTIA-CONNECT actualiza `tools/synthetic-generator`, mantener parches mediante `vendor/synthetic-generator/PATCHES/` y `scripts/update_vendor.sh`.
2. **Telegraf statefile** requiere volumen persistente para no perder estado dedup tras reinicio.
3. **InfluxDB init** es one-shot (`restart: "no"`); permanece como contenedor stopped tras primer deploy.
4. **OpenTelemetry opt-in** vía `OTEL_EXPORTER_OTLP_ENDPOINT` (vacío = deshabilitado en dev).
5. **Calibración real (L-01)** no especificada; usar defaults literatura ASHRAE 62.1 / EN 16798.
