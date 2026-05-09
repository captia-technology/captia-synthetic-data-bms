# Arquitectura — Visión general

> **Última verificación:** 2026-05-10
> **Fuente de verdad:** `docs/specs/synthetic-bms/03-architecture-spec.md`.

## Diagrama de contexto

```mermaid
flowchart LR
    subgraph "captia-bms-network"
        GEN[bms-data-generator<br/>FastAPI :8120]
        MOSQ[Mosquitto :1884]
        TG[Telegraf]
        INF[(InfluxDB :8087<br/>7 buckets)]
        RD[(Redis :6379)]
        GR[Grafana :3001]
        PRO[Prometheus :9090]
        LOK[(Loki :3100)]
        PT[Promtail]
    end
    GEN -- publish<br/>captia/dev/default/ies_simarro/AULAxx/telemetry --> MOSQ
    MOSQ -- mqtt_consumer --> TG
    TG -- write 3 outputs --> INF
    TG -- /metrics :9273 --> PRO
    GR -- query Flux --> INF
    GR <-- HA + cache --> RD
    GR -- LogQL --> LOK
    PT -- Docker logs --> LOK
    GEN -- /metrics :8120 --> PRO
    GEN -- query --> INF
    GEN -- cache --> RD
```

## Capas internas del microservicio

```mermaid
flowchart TB
    subgraph "modules/bms-data-generator"
        API[api/<br/>control · datasets · query · health]
        SVC[services/<br/>runner · dump · query · alias]
        CFG[config.py]
    end
    subgraph "vendor/synthetic-generator (read-only)"
        CORE[core/<br/>runner · registry · types]
        PORTS[ports/]
        SINKS[sinks/<br/>mqtt · file · stdout]
        DOM[domains/bms_classrooms/<br/>physics + plugin]
    end
    subgraph "extensions/bms_calibration"
        CAL[school_calendar]
        FLT[FaultInjector]
        EVS[FaultEventEmitter]
        OVR[physics_overrides]
    end

    SVC --> CORE
    CORE --> SINKS
    CORE --> DOM
    DOM <-.lee config.-> CFG
    DOM -.hooks.-> OVR
    SVC -.usa.-> FLT
    SVC -.usa.-> EVS
    DOM -.usa.-> CAL
```

## Reglas de import

- `vendor/synthetic-generator/core/` **no** importa `domains/`, `sinks/` ni `extensions/`.
- `extensions/bms_calibration/` **no** importa `vendor/.../sinks/` ni `vendor/.../physics/`.
- `modules/bms-data-generator/services/` orquesta `vendor` + `extensions` vía la API pública (registry, ports).
- Los tres paquetes son miembros de un único `pyproject.toml` workspace (`uv sync` los instala juntos).

## Flujos de datos principales

### Caso A — Pipeline IoT en vivo

1. `POST /v1/control/start { mode: "live", aulas: 10 }` → 202 `{ job_id }`.
2. `RunnerService` arranca un thread con `vendor.runner.ScenarioRunner(config)`.
3. Para cada timestamp (5 s):
   - `bms_classrooms.simulate()` produce `DataPoint`.
   - `extensions.faults` (si activo) inyecta fallos según probabilidad.
   - `vendor.sinks.MQTTSinkAdapter` publica a Mosquitto.
4. Telegraf consume MQTT, parsea topic con `processors.regex` (5 tags), escribe `captia_point` en InfluxDB.
5. Tareas Flux downsample → `telemetry_1m → telemetry_15m → telemetry_1h`.
6. Grafana queries → muestra dashboard.

### Caso B — Backfill + dump

1. `POST /v1/datasets/export { months: 12, format: "line_protocol" }` → 202 `{ job_id, output_path }`.
2. `DumpService` ejecuta backfill 365 días con `freq=5min`.
3. `vendor.sinks.FileSinkAdapter` escribe `output/{site_id}_12m.lp`.
4. Compresión gz + checksum sha256.

## Detalles por servicio

| Servicio | Doc | Healthcheck |
|---|---|---|
| `mosquitto` | [`infra/mosquitto/`](https://github.com/captiatechnology/CAPTIA-SYNTHETIC-DATA-BMS/tree/main/infra/mosquitto) | `mosquitto_sub` 1 mensaje |
| `telegraf` | [`infra/telegraf/`](https://github.com/captiatechnology/CAPTIA-SYNTHETIC-DATA-BMS/tree/main/infra/telegraf) | `pgrep telegraf` |
| `influxdb` | [`infra/influxdb/`](https://github.com/captiatechnology/CAPTIA-SYNTHETIC-DATA-BMS/tree/main/infra/influxdb) | `curl /health` |
| `redis` | [`compose/base.yaml`](https://github.com/captiatechnology/CAPTIA-SYNTHETIC-DATA-BMS/blob/main/compose/base.yaml) | `redis-cli ping` |
| `grafana` | [`infra/grafana/`](https://github.com/captiatechnology/CAPTIA-SYNTHETIC-DATA-BMS/tree/main/infra/grafana) | `curl /api/health` |
| `prometheus` | [`infra/prometheus/`](https://github.com/captiatechnology/CAPTIA-SYNTHETIC-DATA-BMS/tree/main/infra/prometheus) | `wget /-/healthy` |
| `loki` | [`infra/loki/`](https://github.com/captiatechnology/CAPTIA-SYNTHETIC-DATA-BMS/tree/main/infra/loki) | `wget /ready` |

## Recursos
- [Decisiones técnicas (ADRs)](../decisions/index.md)
- [Reporte de auditoría top 20](../audit/AUDIT_REPORT.md)
- [Validación E2E](../audit/E2E_VALIDATION_REPORT.md)
