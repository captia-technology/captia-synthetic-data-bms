# Caso G — Calidad de datos con agentes especialistas

> **Última verificación:** 2026-05-10
> **Audiencia:** equipo G2 (Oscar, Vicent, David — pendiente confirmación)
> o G4 nuevo.
> **Capa Medallion primaria:** transversal (audita bronce, plata y oro).
> **Notebooks:** 4 (`notebooks/07_case_G_data_quality_agents/`).

## Objetivo

Definir reglas de calidad sobre las tres capas de todos los equipos y
desarrollar agentes especialistas que las apliquen automáticamente. Trabaja
en oleadas para no bloquearse:

- **Semana 1** — reglas bronce (sobre CSV originales, sin dependencias).
- **Semana 2** — reglas plata (sobre InfluxDB local de cada equipo).
- **Semana 3** — reglas oro + agentes evaluadores (chatbot, MLflow).

## Datos esperados

- Datasets de los demás casos.
- Issues reales documentados en `simarro-prod` como casos de estudio:
  - **H-1**: `site_id` inconsistente entre buckets.
  - **H-2**: `registry.yaml` documenta `centinela_ies_simarro` pero los
    datos usan `ies_simarro`.
  - **H-3**: datos `env=dev` mezclados con producción.
  - **#27**: override `asset_id` del normalizer solo aplica a metadata.
  - **#29**: `--retention 0` aplica 720 h por defecto, no infinita.

## Capas Medallion

Transversal: aplica reglas sobre las tres capas.

| Capa | Reglas | Tooling |
|---|---|---|
| Bronce | rangos, nulos, tipos | `pandera` o GE |
| Plata | completitud, tags, no contaminación | Flux + Python |
| Oro | balance clases, leakage, drift | `sklearn` + KL |

## Notebooks asociados

1. `01_reglas_calidad_bronce.ipynb` — DSL de reglas + GE-style.
2. `02_reglas_calidad_plata_influxdb.ipynb` — queries Flux + Python.
3. `03_reglas_calidad_oro_ml.ipynb` — train/test KL, balance.
4. `04_agentes_especialistas_calidad.ipynb` — agentes mock con 3 tools.

## Agentes especialistas

```python
def validate_silver_layer(asset_id) -> dict
def audit_mlflow_experiment(name) -> dict
def evaluate_chatbot_response(question, expected) -> dict
```

Cada agente devuelve un dict serializable con `verdict ∈ {OK, WARN, FAIL}`.

## Validación

- Las reglas bronce se ejecutan sobre los 3 mocks principales y todas
  pasan.
- Las reglas plata son ejecutables (Flux válido) aunque el bucket esté
  vacío.
- KL train vs test < 1.0 para todas las features del Caso B.

## Errores comunes

1. **Reglas demasiado estrictas** que rechazan datos reales válidos.
2. **No diferenciar warning de error** — el equipo destinatario las ignora.
3. **Reglas que no se versionan** con el dataset.
4. **Aplicar reglas tarde** (semana 4) — nadie tiene tiempo de corregir.

## Reutilización con datos reales

Las reglas Flux son las mismas contra `simarro-prod`. Las reglas de drift
funcionan sobre cualquier nuevo dataset incrementando el dataset de
referencia.

## Coordinación con otros casos

- **Todos los equipos** consumen las reglas G en sus pipelines.
- **Caso F** versiona las reglas en lakeFS.
- **Caso H** — el agente evaluador del chatbot se integra con el chatbot
  G1 para auditar las respuestas.
