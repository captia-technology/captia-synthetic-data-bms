# Validación de calidad de datos

> **Última verificación:** 2026-05-10
> **Caso operacional:** Caso G — `notebooks/07_case_G_data_quality_agents/`.

## Reglas por capa Medallion

### Bronce

Reglas Great-Expectations / pandera sobre CSV originales. Validan:

- Rangos físicos por variable.
- Tipos (int vs float vs bool).
- No nulos en columnas críticas.
- Monotonicidad temporal.
- Sin duplicados (`asset_id, timestamp`).

Implementación: `notebooks/07_*/01_reglas_calidad_bronce.ipynb`.

### Plata

Reglas Flux + Python sobre InfluxDB. Validan:

- Cardinalidad correcta de los 5 tags.
- Cobertura temporal sin gaps > umbral.
- Rangos físicos respetados.
- Variables con metadata (`captia_point_meta` poblado).
- `state_events` no contamina `telemetry`.

Implementación: `notebooks/07_*/02_reglas_calidad_plata_influxdb.ipynb`.

### Oro

Reglas Python sobre datasets ML. Validan:

- Balance de clases en datasets supervisados.
- Sin leakage temporal entre train/val/test.
- KL divergence train/test bajo umbral.
- Modelos referencian `lakefs_tag` en MLflow.

Implementación: `notebooks/07_*/03_reglas_calidad_oro_ml.ipynb`.

## Issues conocidos en simarro-prod

Casos de estudio reales que el Caso G debe documentar / cerrar:

| ID | Descripción |
|---|---|
| H-1 | `site_id` inconsistente entre buckets (`ies_simarro` vs `ies_carlos_iii`). |
| H-2 | `registry.yaml` documenta `centinela_ies_simarro` pero los datos usan `ies_simarro`. |
| H-3 | Datos de entorno `env=dev` mezclados con producción. |
| #27 | Override `asset_id` del normalizer solo aplica a metadata. |
| #29 | `--retention 0` aplica 720 h por defecto, no infinita. |

## Severidad

| Severidad | Comportamiento |
|---|---|
| `error` | Falla el pipeline (CI / deploy). |
| `warning` | Log estructurado + Slack. |
| `info` | Métrica Prometheus. |

## Agentes especialistas

```python
def validate_silver_layer(asset_id) -> dict
def audit_mlflow_experiment(name) -> dict
def evaluate_chatbot_response(question, expected) -> dict
```

Los 3 agentes mock se implementan en
`notebooks/07_*/04_agentes_especialistas_calidad.ipynb`.
