# 09 — Observabilidad de validación física (Fase 9)

## Contexto

Diseño de la capa de observabilidad para que el validador (`07-*`) sea consultable desde Prometheus, Grafana, Loki e InfluxDB. No se modifican métricas existentes (`captia_bms_*`); todo va con prefijo `captia_physics_*` y a un nuevo bucket InfluxDB.

**Cross-ref**: `docs/specs/synthetic-bms/05-observability-spec.md` (existente — métricas `captia_bms_*`, dashboards 4 actuales). Este documento **extiende**, no reemplaza.

## Métricas Prometheus (`captia_physics_*`)

### Counters

```yaml
captia_physics_rule_evaluations_total:
  type: counter
  labels: [rule_id, severity, asset_id, result]
  description: |
    Número total de evaluaciones de cada regla, etiquetadas por resultado (passed|failed|skipped).
  emitted_by: bms_physics_validator (en finalize() y por window).
  example: |
    captia_physics_rule_evaluations_total{rule_id="R-CO2-01",severity="warning",asset_id="AULA01",result="passed"} 24
    captia_physics_rule_evaluations_total{rule_id="R-OCC-01",severity="error",asset_id="*",result="failed"} 1

captia_physics_validation_runs_total:
  type: counter
  labels: [scenario, mode]
  description: Total de runs de validación completos.
  example: captia_physics_validation_runs_total{scenario="bms_v1_caseB_consumption",mode="post_run"} 12

captia_physics_recommendations_total:
  type: counter
  labels: [priority, source_rule]
  description: Recomendaciones generadas por el RealismScorer.
```

### Gauges

```yaml
captia_physics_realism_score_global:
  type: gauge
  labels: []
  description: Score interno global (0..1). Última evaluación.
  example: captia_physics_realism_score_global 0.94

captia_physics_realism_score_dimension:
  type: gauge
  labels: [dimension]
  description: Score por dimensión (D1..D10).
  example: |
    captia_physics_realism_score_dimension{dimension="D1_thermal_coherence"} 1.00
    captia_physics_realism_score_dimension{dimension="D7_faults"} NaN  (unscored)

captia_physics_rule_evidence:
  type: gauge
  labels: [rule_id, asset_id, metric_name]
  description: Última métrica de evidencia por regla y aula.
  example: |
    captia_physics_rule_evidence{rule_id="R-CO2-01",asset_id="AULA01",metric_name="co2_slope_per_occupancy"} 6.2
    captia_physics_rule_evidence{rule_id="R-EN-01",asset_id="AULA01",metric_name="conservation_error_pct"} 0.003

captia_physics_dimension_blocked:
  type: gauge
  labels: [dimension, blocking_issue]
  description: 1 si la dimensión está bloqueada por un L-PV-NN.
  example: captia_physics_dimension_blocked{dimension="D7_faults",blocking_issue="L-PV-02"} 1
```

### Histograms

```yaml
captia_physics_validation_duration_seconds:
  type: histogram
  labels: [mode]
  buckets: [0.1, 0.5, 1, 5, 10, 30, 60, 300]
  description: Tiempo total de validación de un dataset.

captia_physics_window_evaluation_duration_seconds:
  type: histogram
  labels: [rule_family]
  buckets: [0.001, 0.01, 0.1, 1, 10]
  description: Tiempo por evaluación de una ventana (live mode).

captia_physics_evidence_distribution:
  type: histogram
  labels: [rule_id, metric_name]
  buckets: dinámicos por regla
  description: |
    Distribución de valores de evidencia. Útil para gauge promedio + percentiles.
    Ejemplo: histogram de co2_slope_per_occupancy → ver mediana y p95.
```

### Métricas derivadas (recording rules Prometheus)

```yaml
# infra/prometheus/rules/bms_physics_recording.rules.yml (nuevo)
groups:
  - name: bms_physics_recording
    interval: 1m
    rules:
      - record: captia_physics_rule_pass_rate
        expr: |
          sum by (rule_id) (rate(captia_physics_rule_evaluations_total{result="passed"}[1h]))
          /
          sum by (rule_id) (rate(captia_physics_rule_evaluations_total[1h]))

      - record: captia_physics_failed_rules_count
        expr: |
          count by () (captia_physics_rule_pass_rate < 0.95)

      - record: captia_physics_score_trend_24h
        expr: |
          captia_physics_realism_score_global - captia_physics_realism_score_global offset 24h
```

## Alertas (`infra/prometheus/rules/bms_physics_alerts.rules.yml`)

```yaml
groups:
  - name: bms_physics_alerts
    interval: 1m
    rules:
      - alert: PhysicsRealismScoreLow
        expr: captia_physics_realism_score_global < 0.70
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Realism score < 0.70 — generador no plausible"
          description: "Score actual {{ $value }}. Revisar reglas error fallidas."

      - alert: PhysicsRealismScoreDegraded
        expr: captia_physics_realism_score_global < 0.85 and captia_physics_realism_score_global >= 0.70
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "Realism score degradado entre 0.70 y 0.85"
          description: "Score: {{ $value }}. Revisar `diagnostics`."

      - alert: PhysicsEnergyBalanceOff
        expr: |
          avg by (asset_id) (
            captia_physics_rule_evidence{rule_id="R-EN-01",metric_name="conservation_error_pct"}
          ) > 0.05
        for: 1h
        labels:
          severity: error
        annotations:
          summary: "{{ $labels.asset_id }} energy conservation error > 5%"

      - alert: PhysicsHVACShortCycleHigh
        expr: |
          avg by (asset_id) (
            captia_physics_rule_evidence{rule_id="R-HVAC-EN-03",metric_name="short_cycle_ratio"}
          ) > 0.30
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "{{ $labels.asset_id }} short cycle ratio > 30% (L-PV-07 sin resolver)"

      - alert: PhysicsCO2SlopeAnomalous
        expr: |
          avg by (asset_id) (
            captia_physics_rule_evidence{rule_id="R-CO2-01",metric_name="co2_slope_per_occupancy"}
          ) > 15 OR
          avg by (asset_id) (
            captia_physics_rule_evidence{rule_id="R-CO2-01",metric_name="co2_slope_per_occupancy"}
          ) < 1
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "CO₂ slope per occupancy fuera de rango razonable [1, 15] ppm/min·persona"
```

## Logs estructurados (Loki)

El validador emite logs JSON tras cada window (live) o tras cada validate_batch (post-run):

```json
{
  "ts": "2026-01-15T08:30:00Z",
  "level": "INFO",
  "logger": "bms_physics_validator",
  "message": "validation window completed",
  "run_id": "abc123def456",
  "asset_id": "AULA01",
  "window_start": "2026-01-15T07:30:00Z",
  "window_end": "2026-01-15T08:30:00Z",
  "rules_evaluated": 24,
  "rules_passed": 23,
  "rules_failed": 1,
  "failed_rules": [
    {"rule_id": "R-OCC-01", "evidence_metric": "occupancy_mean_holiday", "value": 8.4, "expected_max": 1}
  ]
}
```

Promtail está ya configurado para parsear JSON de bms-data-generator (`infra/observability/promtail/promtail-config.yml`); añadir `bms_physics_validator` al mismo pipeline.

**LogQL queries útiles** (en dashboard nuevo):

```logql
# Reglas error que fallaron en la última hora
{compose_project="captia-bms", logger="bms_physics_validator"}
  | json
  | level = "ERROR"
  | __error__ = ""

# Tendencia de validations completed
sum(rate({logger="bms_physics_validator"} | json | message = "validation window completed" [5m]))

# Top 5 reglas que más fallan
topk(5,
  count by (rule_id) (
    {logger="bms_physics_validator"}
      | json
      | rules_failed > 0
      | unwrap failed_rules
  )
)
```

## Bucket InfluxDB nuevo: `physics_metrics`

```yaml
bucket: physics_metrics
retention: 90d
purpose: |
  Almacena métricas derivadas de validación física, calculadas hourly por una Flux task.
  Permite consultas históricas y dashboards que comparan score a lo largo del tiempo.
```

### Schema

```text
measurement: captia_physics_point
tags (5, MISMO schema que captia_point):
  captia_env, domain_id, site_id, asset_id, variable
field:
  value: float
```

**Convención de variables** (sub-namespace `physics.*`):

| Variable | Descripción | Unit |
|----------|-------------|------|
| `physics.score_global` | Score interno global (asset_id="*") | unitless [0..1] |
| `physics.score_d1_thermal` | Score dimensión D1 | unitless |
| ... | (D2..D10) | unitless |
| `physics.energy_balance_error_pct` | R-EN-01 evidencia | % |
| `physics.hvac_short_cycle_ratio` | R-HVAC-EN-03 | unitless [0..1] |
| `physics.co2_slope_per_occupancy_ppm_min_person` | R-CO2-01 | ppm/min/persona |
| `physics.thermal_response_tau_min` | R-T-02 | min |
| `physics.cooling_dehumid_slope_pct_min` | R-RH-02 | %RH/min (negativo esperado) |
| `physics.occupancy_holiday_mean` | R-OCC-01 | persons |
| `physics.fault_signature_match` | R-FAULT-* (cuando exista) | unitless [0..1] |

**Ejemplo de write line protocol**:

```text
captia_physics_point,captia_env=dev,domain_id=bms_classrooms,site_id=ies_simarro,asset_id=AULA01,variable=physics.score_global value=0.94 1737000000000000000
```

### Flux task `physics_validation_hourly.flux`

```text
// /infra/influxdb/tasks/physics_validation_hourly.flux

option task = {
  name: "physics_validation_hourly",
  every: 1h,
}

// Calcula energy balance error: |Σpower·dt - Δenergy| / Δenergy
// Por aula, en ventana 1h.

power_sum = from(bucket: "telemetry_1m")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "captia_point" and r.variable == "power" and r._field == "value")
  |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
  |> map(fn: (r) => ({ r with energy_implied_kwh: r._value * 1.0 / 1000.0 }))  // dt = 1h

energy_actual_change = from(bucket: "telemetry_1h")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "captia_point" and r.variable == "energy" and r._field == "value")
  |> difference()

joined = join(tables: { power: power_sum, energy: energy_actual_change }, on: ["asset_id"])
  |> map(fn: (r) => ({
    _time: r._time,
    asset_id: r.asset_id,
    captia_env: r.captia_env,
    domain_id: r.domain_id,
    site_id: r.site_id,
    variable: "physics.energy_balance_error_pct",
    _measurement: "captia_physics_point",
    _field: "value",
    _value: math.abs(x: r.energy_implied_kwh - r._value) / r._value * 100.0,
  }))
  |> to(bucket: "physics_metrics", org: "captia")
```

**Consideraciones**:
- La task debe correr cada hora (alineada a hora natural).
- Reusar `aggregateWindow` para CO₂ slope, occupancy mean, etc.
- Cada regla observable tiene un sub-task; alternativamente una task monolítica con `from(bucket).pivot(...)`.
- **Versionado**: tasks versionadas en `infra/influxdb/tasks/` (mismo patrón que las 5 existentes).

### Tasks adicionales propuestas

| Task | Calcula | Frecuencia |
|------|---------|-----------|
| `physics_co2_slope_hourly.flux` | R-CO2-01 evidence per asset | 1h |
| `physics_hvac_cycle_hourly.flux` | R-HVAC-EN-03 short_cycle_ratio | 1h |
| `physics_occupancy_holiday_daily.flux` | R-OCC-01 mean en festivos detectados | 1d |
| `physics_thermal_response_daily.flux` | R-T-02 tau estimado | 1d |
| `physics_score_global_5m.flux` | rollup de score_global recibido vía Prometheus → Influx | 5m |

## Nuevo dashboard Grafana: `bms_physics_validation.json`

```text
[Panel 1] Realism score (single stat, gauge 0..1)
  Datasource: Prometheus
  Query: captia_physics_realism_score_global
  Thresholds: 0.50 red, 0.70 orange, 0.85 yellow, 0.95 green

[Panel 2] Score por dimensión (bar chart)
  Datasource: Prometheus
  Query: captia_physics_realism_score_dimension
  Etiqueta dimensión en eje X

[Panel 3] Tendencia score 24h (time series)
  Datasource: InfluxDB physics_metrics
  Query Flux:
    from(bucket:"physics_metrics")
      |> range(start: -24h)
      |> filter(fn:(r) => r.variable == "physics.score_global")

[Panel 4] Reglas que más fallan (table)
  Datasource: Prometheus
  Query:
    topk(10, sum by (rule_id) (
      rate(captia_physics_rule_evaluations_total{result="failed"}[1h])
    ))

[Panel 5] Energy balance error por aula (heatmap)
  Datasource: Prometheus
  Query: captia_physics_rule_evidence{rule_id="R-EN-01",metric_name="conservation_error_pct"}
  Eje X: tiempo, eje Y: asset_id, color: error %

[Panel 6] HVAC short cycle ratio por aula (time series)
  Datasource: Prometheus
  Query: avg by (asset_id) (
    captia_physics_rule_evidence{rule_id="R-HVAC-EN-03",metric_name="short_cycle_ratio"}
  )

[Panel 7] CO₂ slope vs occupancy (scatter / time series)
  Datasource: InfluxDB physics_metrics
  Query: variable == "physics.co2_slope_per_occupancy_ppm_min_person"

[Panel 8] Series con overlays (CO₂, occupancy, hvac_enable) — variable AULA selectable
  Datasource: InfluxDB telemetry / state_events
  Multi-axis chart; subraya causalidad visualmente.

[Panel 9] Eventos de avería (time series + annotations)
  Datasource: InfluxDB state_events bucket
  Query: variable LIKE 'fault.*'
  (Vacío hasta resolver L-PV-02)

[Panel 10] Validations completed (Loki)
  Datasource: Loki
  Query: rate({logger="bms_physics_validator"} | json | message = "validation window completed" [5m])

[Panel 11] Diagnostics low-confidence (table)
  Datasource: Prometheus
  Query: captia_physics_rule_evidence{rule_id=~"R-(RH-02|HVAC-EN-03|VLV-02)"}

[Panel 12] Recomendaciones del scorer (table)
  Datasource: Loki
  Query: {logger="bms_physics_validator"} | json | message = "scorer recommendations"
```

**Provisioning**:
- Fichero: `infra/grafana/dashboards/bms_physics_validation.json`.
- UID: `bms-physics-validation` (para deep-links desde alertas).
- Folder: `BMS / Physics Validation`.

## Variables de dashboard

```yaml
$asset_id: query Prometheus label "asset_id" from captia_physics_*
$dimension: static [D1, D2, ..., D10]
$rule_id: query Prometheus label "rule_id"
$severity: static [error, warning, info]
$mode: static [live, post_run]
```

## Integración con alertas existentes

Alertas existentes (`captia_bms_*`):
- `BMSGeneratorDown`
- `BMSPublishErrorRateHigh`
- `BMSDumpExportStuck`

Las nuevas (`captia_physics_*`) coexisten en el mismo Alertmanager:
- Channel: misma config, no se requiere routing nuevo.
- Inhibition: si `BMSGeneratorDown` está activa, suprimir todas las `Physics*` (sin generador no hay validación).

## Resumen de cambios infraestructura

| Componente | Cambio | Fichero |
|------------|--------|---------|
| `metrics.py` | Añadir registry de `captia_physics_*` (counters, gauges, histograms) | `modules/bms-data-generator/src/bms_data_generator/metrics.py` |
| Validator | Emitir métricas tras cada window | `extensions/bms_physics_validator/src/bms_physics_validator/metrics_emitter.py` (nuevo) |
| InfluxDB | Crear bucket `physics_metrics` (90d) | `infra/influxdb/init/init_buckets_tasks.sh` línea 67-67 (insert) |
| InfluxDB | Crear Flux tasks `physics_*.flux` | `infra/influxdb/tasks/` |
| Prometheus | Añadir recording rules y alert rules | `infra/prometheus/rules/bms_physics_recording.rules.yml`, `bms_physics_alerts.rules.yml` (nuevos) |
| Grafana | Provisionar dashboard nuevo | `infra/grafana/dashboards/bms_physics_validation.json` (nuevo) |
| Promtail | Confirma scrape de logger `bms_physics_validator` | `infra/observability/promtail/promtail-config.yml` (revisar regex existente) |
| Alertmanager | Inhibition rules nuevas (si captia_bms_down → suprimir physics_*) | `infra/observability/alertmanager/...` (si existe) |

## Política de retención

- Bucket `physics_metrics`: 90 días (alineado con `state_events`).
- Métricas Prometheus: heredan retention global Prometheus (7d default).
- Logs Loki: heredan retention 30d.

## Cómo el dashboard responde a las preguntas físicas

| Pregunta usuario | Panel(es) que responde |
|-----------------|------------------------|
| "¿El generador es plausible hoy?" | Panel 1 (score global) |
| "¿Qué dimensión está peor?" | Panel 2 (bar chart) |
| "¿Está empeorando con el tiempo?" | Panel 3 (trend) |
| "¿Qué reglas fallan más?" | Panel 4 (top fails) |
| "¿Qué aula tiene problemas energéticos?" | Panel 5 (energy balance heatmap) |
| "¿Hay short-cycle?" | Panel 6 |
| "¿La causalidad ocupancy → CO₂ es realista?" | Panel 8 (overlays) |
| "¿Las averías se materializan?" | Panel 9 (vacío hoy → confirma L-PV-02) |
| "¿Qué hago para mejorar el score?" | Panel 12 (recomendaciones) |

## Coste de la observabilidad

- **CPU**: Flux tasks ~5% por aula·hora (estimado). Para 70 aulas: ~3.5 CPU·s/h. Despreciable.
- **Storage**: bucket `physics_metrics`: ~10 KB/aula/día → 70 aulas · 90 días · 10 KB = ~63 MB. Despreciable.
- **Latencia métricas**: Prometheus scrape 15s. Para alertas críticas, latencia ≤ 30s.
- **Latencia validación**: depende de mode (live: window_seconds; post-run: depende de tamaño dataset).
